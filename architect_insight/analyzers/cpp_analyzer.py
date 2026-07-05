"""
cpp_analyzer.py
-----------------
Analyse les fichiers C++ en utilisant tree-sitter-cpp
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    import tree_sitter_cpp as tscpp
    from tree_sitter import Language, Parser
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False

@dataclass
class CPPFunctionMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_params: int
    class_name: str | None = None

@dataclass
class CPPClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int

@dataclass
class CPPFileMetrics:
    path: str
    num_imports: int
    functions: list[CPPFunctionMetrics]
    classes: list[CPPClassMetrics]
    num_lines: int
    parse_error: str | None = None

def _count_branches_cpp(node) -> int:
    """Compte approximativement le nombre de branches dans un fichier C++."""
    count = 1
    if not CPP_AVAILABLE:
        return 0
    
    for child in node.children:
        child_type = child.type
        if child_type in ["if_statement", "for_statement", "while_statement", 
                          "do_statement", "switch_statement", "case_statement"]:
            count += 1
        count += _count_branches_cpp(child)
    return count

def _parse_cpp_file(filepath: str) -> CPPFileMetrics:
    """Analyse un fichier C++."""
    if not CPP_AVAILABLE:
        return CPPFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=0,
            parse_error="tree-sitter-cpp non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return CPPFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        CPP_LANGUAGE = Language(tscpp.language())
        parser = Parser(CPP_LANGUAGE)
        tree = parser.parse(bytes(source, "utf-8"))
        root = tree.root_node
        
        functions = []
        classes = []
        imports = 0
        
        def walk(node, class_name: str | None = None):
            nonlocal imports
            if node.type == "function_definition":
                name_node = node.child_by_field_name("declarator")
                name = "unknown"
                if name_node:
                    name = name_node.text.decode().split("(")[0].strip()
                params = 0
                param_node = node.child_by_field_name("parameters")
                if param_node:
                    for child in param_node.children:
                        if child.type == "parameter_declaration":
                            params += 1
                complexity = _count_branches_cpp(node)
                functions.append(CPPFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    class_name=class_name
                ))
            elif node.type == "class_specifier":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                body = node.child_by_field_name("body")
                method_count = 0
                if body:
                    for child in body.children:
                        if child.type in ["function_definition", "method_definition"]:
                            method_count += 1
                classes.append(CPPClassMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    num_methods=method_count
                ))
                if body:
                    for child in body.children:
                        walk(child, name)
            elif node.type == "preproc_include":
                imports += 1
            
            for child in node.children:
                walk(child, class_name)
        
        walk(root)
        
        return CPPFileMetrics(
            path=filepath,
            num_imports=imports,
            functions=functions,
            classes=classes,
            num_lines=num_lines,
        )
    except Exception as e:
        return CPPFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_cpp_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers C++ dans un répertoire."""
    all_files = []
    total_functions = 0
    total_classes = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "target"}]
        for file in files:
            if file.endswith((".cpp", ".cc", ".cxx", ".h", ".hpp")):
                full_path = os.path.join(root, file)
                metrics = _parse_cpp_file(full_path)
                all_files.append(metrics)
                total_functions += len(metrics.functions)
                total_classes += len(metrics.classes)
    
    return {
        "files_analyzed": len(all_files),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "has_cpp_analysis": CPP_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20]
    }