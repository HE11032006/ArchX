"""
cs_analyzer.py
----------------
Analyse les fichiers C# en utilisant tree-sitter-c-sharp
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    import tree_sitter_c_sharp as tscs
    from tree_sitter import Language, Parser
    CS_AVAILABLE = True
except ImportError:
    CS_AVAILABLE = False

@dataclass
class CSMethodMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_params: int
    class_name: str | None = None

@dataclass
class CSClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int

@dataclass
class CSFileMetrics:
    path: str
    num_imports: int
    methods: list[CSMethodMetrics]
    classes: list[CSClassMetrics]
    num_lines: int
    parse_error: str | None = None

def _count_branches_cs(node) -> int:
    """Compte approximativement le nombre de branches dans un fichier C#."""
    count = 1
    if not CS_AVAILABLE:
        return 0
    
    for child in node.children:
        child_type = child.type
        if child_type in ["if_statement", "for_statement", "foreach_statement", 
                          "while_statement", "switch_statement", "case_switch_label"]:
            count += 1
        count += _count_branches_cs(child)
    return count

def _parse_cs_file(filepath: str) -> CSFileMetrics:
    """Analyse un fichier C#."""
    if not CS_AVAILABLE:
        return CSFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=0,
            parse_error="tree-sitter-c-sharp non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return CSFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        CS_LANGUAGE = Language(tscs.language())
        parser = Parser(CS_LANGUAGE)
        tree = parser.parse(bytes(source, "utf-8"))
        root = tree.root_node
        
        methods = []
        classes = []
        imports = 0
        
        def walk(node, class_name: str | None = None):
            nonlocal imports
            if node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                param_node = node.child_by_field_name("parameters")
                if param_node:
                    for child in param_node.children:
                        if child.type == "parameter":
                            params += 1
                complexity = _count_branches_cs(node)
                methods.append(CSMethodMetrics(
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
                body = node.child_by_field_name("body")
                method_count = 0
                if body:
                    for child in body.children:
                        if child.type == "method_declaration":
                            method_count += 1
                classes.append(CSClassMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    num_methods=method_count
                ))
                if body:
                    for child in body.children:
                        walk(child, name)
            elif node.type == "using_directive":
                imports += 1
            
            for child in node.children:
                walk(child, class_name)
        
        walk(root)
        
        return CSFileMetrics(
            path=filepath,
            num_imports=imports,
            methods=methods,
            classes=classes,
            num_lines=num_lines,
        )
    except Exception as e:
        return CSFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_cs_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers C# dans un répertoire."""
    all_files = []
    total_methods = 0
    total_classes = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "bin", "obj"}]
        for file in files:
            if file.endswith(".cs"):
                full_path = os.path.join(root, file)
                metrics = _parse_cs_file(full_path)
                all_files.append(metrics)
                total_methods += len(metrics.methods)
                total_classes += len(metrics.classes)
    
    return {
        "files_analyzed": len(all_files),
        "total_methods": total_methods,
        "total_classes": total_classes,
        "has_cs_analysis": CS_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20]
    }