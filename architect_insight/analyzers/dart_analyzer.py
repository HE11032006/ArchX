"""
dart_analyzer.py
------------------
Analyse les fichiers Dart en utilisant tree-sitter
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    import tree_sitter_dart as tsdart
    from tree_sitter import Language, Parser
    DART_AVAILABLE = True
except ImportError:
    DART_AVAILABLE = False

@dataclass
class DartFunctionMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_params: int
    class_name: str | None = None

@dataclass
class DartClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int

@dataclass
class DartFileMetrics:
    path: str
    num_imports: int
    functions: list[DartFunctionMetrics]
    classes: list[DartClassMetrics]
    num_lines: int
    parse_error: str | None = None

def _count_branches_dart(node) -> int:
    """Compte approximativement le nombre de branches dans un fichier Dart."""
    count = 1
    if not DART_AVAILABLE:
        return 0
    
    for child in node.children:
        child_type = child.type
        if child_type in ["if_statement", "for_statement", "while_statement", 
                          "do_statement", "switch_statement", "conditional_expression"]:
            count += 1
        count += _count_branches_dart(child)
    return count

def _parse_dart_file(filepath: str) -> DartFileMetrics:
    """Analyse un fichier Dart."""
    if not DART_AVAILABLE:
        return DartFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=0,
            parse_error="tree-sitter-dart non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return DartFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        DART_LANGUAGE = Language(tsdart.language())
        parser = Parser(DART_LANGUAGE)
        tree = parser.parse(bytes(source, "utf-8"))
        root = tree.root_node
        
        functions = []
        classes = []
        imports = 0
        
        def walk(node, class_name: str | None = None):
            nonlocal imports
            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                # Compter les paramètres (approximatif)
                for child in node.children:
                    if child.type == "formal_parameter":
                        params += 1
                complexity = _count_branches_dart(node)
                functions.append(DartFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    class_name=class_name
                ))
            elif node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                complexity = _count_branches_dart(node)
                functions.append(DartFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    class_name=class_name
                ))
            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                class_body = node.child_by_field_name("body")
                method_count = 0
                if class_body:
                    for child in class_body.children:
                        if child.type == "method_declaration":
                            method_count += 1
                classes.append(DartClassMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    num_methods=method_count
                ))
                if class_body:
                    for child in class_body.children:
                        walk(child, name)
            elif node.type == "import_statement":
                imports += 1
            
            for child in node.children:
                if child.type not in ["class_declaration"]:
                    walk(child, class_name)
        
        walk(root)
        
        return DartFileMetrics(
            path=filepath,
            num_imports=imports,
            functions=functions,
            classes=classes,
            num_lines=num_lines,
        )
    except Exception as e:
        return DartFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_dart_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers Dart dans un répertoire."""
    all_files = []
    total_functions = 0
    total_classes = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "target"}]
        for file in files:
            if file.endswith(".dart"):
                full_path = os.path.join(root, file)
                metrics = _parse_dart_file(full_path)
                all_files.append(metrics)
                total_functions += len(metrics.functions)
                total_classes += len(metrics.classes)
    
    return {
        "files_analyzed": len(all_files),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "has_dart_analysis": DART_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20]
    }