"""
java_analyzer.py
------------------
Analyse les fichiers Java avec tree-sitter-java (remplace l'ancienne
dépendance sur `javaparser`, qui n'existe pas sur PyPI sous ce nom — voir
requirements.txt). Les dataclasses reprennent volontairement la même forme
que architect_insight/metrics/complexity.py::FunctionMetrics/ClassMetrics/
FileMetrics (mêmes noms de champs, y compris `functions` et non `methods`)
pour que detect_anti_patterns() (patterns.py, full duck-typed) fonctionne
sans aucune modification sur la sortie de cet analyseur.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    import tree_sitter_java as tsjava
    from tree_sitter import Language, Parser
    JAVA_AVAILABLE = True
except ImportError:
    JAVA_AVAILABLE = False


@dataclass
class JavaFunctionMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_lines: int
    num_params: int
    class_name: str | None = None

    @property
    def qualified_name(self) -> str:
        return f"{self.class_name}.{self.name}" if self.class_name else self.name


@dataclass
class JavaClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int
    num_lines: int
    method_names: list[str] = field(default_factory=list)


@dataclass
class JavaFileMetrics:
    path: str
    num_imports: int
    functions: list[JavaFunctionMetrics]
    classes: list[JavaClassMetrics]
    num_lines: int
    parse_error: str | None = None


# Node types that add a branch to McCabe complexity — verified against a real
# parse with tree-sitter-java 0.23.5 (ternary_expression included as a bonus;
# switch_expression covers both switch statements and switch expressions in
# this grammar, there is no separate switch_statement node type).
_BRANCH_NODE_TYPES = {
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
    "switch_expression",
    "switch_block_statement_group",
    "catch_clause",
    "ternary_expression",
}


def _count_branches_java(node) -> int:
    """Compte approximativement le nombre de branches dans un noeud Java."""
    count = 1
    for child in node.children:
        if child.type in _BRANCH_NODE_TYPES:
            count += 1
        count += _count_branches_java(child) - 1
    return count


def _num_params(method_node) -> int:
    params_node = method_node.child_by_field_name("parameters")
    if not params_node:
        return 0
    return sum(1 for c in params_node.children if c.type == "formal_parameter")


def _parse_java_file(filepath: str, repo_path: str) -> JavaFileMetrics:
    """Analyse un fichier Java. `repo_path` sert uniquement à stocker un chemin
    relatif dans `path` (cohérent avec les entrées Python de collector.py, qui
    utilisent aussi des chemins relatifs — nécessaire pour fusionner sans
    collision dans le même tableau `anti_patterns`)."""
    rel_path = os.path.relpath(filepath, repo_path)

    if not JAVA_AVAILABLE:
        return JavaFileMetrics(
            path=rel_path, num_imports=0, functions=[], classes=[],
            num_lines=0, parse_error="tree-sitter-java non installé",
        )

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return JavaFileMetrics(
            path=rel_path, num_imports=0, functions=[], classes=[],
            num_lines=0, parse_error=f"Erreur de lecture: {e}",
        )

    num_lines = source.count("\n") + 1

    try:
        java_language = Language(tsjava.language())
        parser = Parser(java_language)
        tree = parser.parse(bytes(source, "utf-8"))
        root = tree.root_node

        functions: list[JavaFunctionMetrics] = []
        classes: list[JavaClassMetrics] = []
        imports = 0

        def walk(node, class_name: str | None = None) -> None:
            nonlocal imports

            if node.type in ("method_declaration", "constructor_declaration"):
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                lineno = node.start_point[0] + 1
                end_lineno = node.end_point[0] + 1
                functions.append(JavaFunctionMetrics(
                    name=name,
                    lineno=lineno,
                    end_lineno=end_lineno,
                    complexity=_count_branches_java(node),
                    num_lines=end_lineno - lineno + 1,
                    num_params=_num_params(node),
                    class_name=class_name,
                ))
                return  # ne pas redescendre : évite de compter les méthodes des classes locales/anonymes en double

            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                body = node.child_by_field_name("body")
                method_names = [
                    c.child_by_field_name("name").text.decode()
                    for c in (body.children if body else [])
                    if c.type in ("method_declaration", "constructor_declaration")
                    and c.child_by_field_name("name")
                ]
                lineno = node.start_point[0] + 1
                end_lineno = node.end_point[0] + 1
                classes.append(JavaClassMetrics(
                    name=name,
                    lineno=lineno,
                    end_lineno=end_lineno,
                    num_methods=len(method_names),
                    num_lines=end_lineno - lineno + 1,
                    method_names=method_names,
                ))
                if body:
                    for child in body.children:
                        walk(child, name)
                return

            if node.type == "import_declaration":
                imports += 1

            for child in node.children:
                walk(child, class_name)

        walk(root)

        return JavaFileMetrics(
            path=rel_path,
            num_imports=imports,
            functions=functions,
            classes=classes,
            num_lines=num_lines,
        )
    except Exception as e:
        return JavaFileMetrics(
            path=rel_path, num_imports=0, functions=[], classes=[],
            num_lines=num_lines, parse_error=f"Erreur de parsing: {e}",
        )


def analyze_java_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers Java dans un répertoire."""
    all_files: list[JavaFileMetrics] = []
    total_methods = 0
    total_classes = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target", "build"}]
        for file in files:
            if file.endswith(".java"):
                full_path = os.path.join(root, file)
                metrics = _parse_java_file(full_path, repo_path)
                all_files.append(metrics)
                total_methods += len(metrics.functions)
                total_classes += len(metrics.classes)

    return {
        "files_analyzed": len(all_files),
        "total_methods": total_methods,
        "total_classes": total_classes,
        "has_java_analysis": JAVA_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20],
    }
