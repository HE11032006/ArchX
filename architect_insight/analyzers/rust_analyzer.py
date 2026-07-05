"""
rust_analyzer.py
------------------
Analyse les fichiers Rust en utilisant tree-sitter-rust
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    import tree_sitter_rust as tsrust
    from tree_sitter import Language, Parser
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False

@dataclass
class RustFunctionMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_params: int
    struct_name: str | None = None

@dataclass
class RustStructMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_fields: int

@dataclass
class RustFileMetrics:
    path: str
    num_imports: int
    functions: list[RustFunctionMetrics]
    structs: list[RustStructMetrics]
    num_lines: int
    parse_error: str | None = None

def _count_branches_rust(node) -> int:
    """Compte approximativement le nombre de branches dans un fichier Rust."""
    count = 1
    if not RUST_AVAILABLE:
        return 0
    
    for child in node.children:
        child_type = child.type
        if child_type in ["if_expression", "for_expression", "while_expression", 
                          "loop_expression", "match_expression", "match_arm"]:
            count += 1
        count += _count_branches_rust(child)
    return count

def _parse_rust_file(filepath: str) -> RustFileMetrics:
    """Analyse un fichier Rust."""
    if not RUST_AVAILABLE:
        return RustFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            structs=[],
            num_lines=0,
            parse_error="tree-sitter-rust non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return RustFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            structs=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        RUST_LANGUAGE = Language(tsrust.language())
        parser = Parser(RUST_LANGUAGE)
        tree = parser.parse(bytes(source, "utf-8"))
        root = tree.root_node
        
        functions = []
        structs = []
        imports = 0
        
        def walk(node, struct_name: str | None = None):
            nonlocal imports
            if node.type == "function_item":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                param_node = node.child_by_field_name("parameters")
                if param_node:
                    for child in param_node.children:
                        if child.type == "parameter":
                            params += 1
                complexity = _count_branches_rust(node)
                functions.append(RustFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    struct_name=struct_name
                ))
            elif node.type == "struct_item":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                fields_count = 0
                field_list = node.child_by_field_name("fields")
                if field_list:
                    for child in field_list.children:
                        if child.type == "field_declaration":
                            fields_count += 1
                structs.append(RustStructMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    num_fields=fields_count
                ))
            elif node.type == "use_declaration":
                imports += 1
            elif node.type == "use_list":
                imports += 1
            
            for child in node.children:
                walk(child, struct_name)
        
        walk(root)
        
        return RustFileMetrics(
            path=filepath,
            num_imports=imports,
            functions=functions,
            structs=structs,
            num_lines=num_lines,
        )
    except Exception as e:
        return RustFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            structs=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_rust_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers Rust dans un répertoire."""
    all_files = []
    total_functions = 0
    total_structs = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target"}]
        for file in files:
            if file.endswith(".rs"):
                full_path = os.path.join(root, file)
                metrics = _parse_rust_file(full_path)
                all_files.append(metrics)
                total_functions += len(metrics.functions)
                total_structs += len(metrics.structs)
    
    return {
        "files_analyzed": len(all_files),
        "total_functions": total_functions,
        "total_structs": total_structs,
        "has_rust_analysis": RUST_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20]
    }