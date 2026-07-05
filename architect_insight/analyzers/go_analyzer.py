"""
go_analyzer.py
----------------
Analyse les fichiers Go en utilisant tree-sitter-go
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    import tree_sitter_go as tsgo
    from tree_sitter import Language, Parser
    GO_AVAILABLE = True
except ImportError:
    GO_AVAILABLE = False

@dataclass
class GoFunctionMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_params: int
    struct_name: str | None = None

@dataclass
class GoStructMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_fields: int
    num_methods: int

@dataclass
class GoFileMetrics:
    path: str
    num_imports: int
    functions: list[GoFunctionMetrics]
    structs: list[GoStructMetrics]
    num_lines: int
    parse_error: str | None = None

def _count_branches_go(node) -> int:
    """Compte approximativement le nombre de branches dans un fichier Go."""
    count = 1
    if not GO_AVAILABLE:
        return 0
    
    for child in node.children:
        child_type = child.type
        if child_type in ["if_statement", "for_statement", "switch_statement", 
                          "select_statement", "case_statement"]:
            count += 1
        count += _count_branches_go(child)
    return count

def _parse_go_file(filepath: str) -> GoFileMetrics:
    """Analyse un fichier Go."""
    if not GO_AVAILABLE:
        return GoFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            structs=[],
            num_lines=0,
            parse_error="tree-sitter-go non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return GoFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            structs=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        GO_LANGUAGE = Language(tsgo.language())
        parser = Parser(GO_LANGUAGE)
        tree = parser.parse(bytes(source, "utf-8"))
        root = tree.root_node
        
        functions = []
        structs = []
        imports = 0
        
        def walk(node, struct_name: str | None = None):
            nonlocal imports
            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                param_node = node.child_by_field_name("parameters")
                if param_node:
                    for child in param_node.children:
                        if child.type == "parameter_declaration":
                            params += 1
                complexity = _count_branches_go(node)
                functions.append(GoFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    struct_name=struct_name
                ))
            elif node.type == "method_declaration":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                complexity = _count_branches_go(node)
                functions.append(GoFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    struct_name=struct_name
                ))
            elif node.type == "type_declaration":
                for child in node.children:
                    if child.type == "type_spec":
                        name_node = child.child_by_field_name("name")
                        name = name_node.text.decode() if name_node else "anonymous"
                        struct_body = child.child_by_field_name("type")
                        fields_count = 0
                        if struct_body:
                            for field in struct_body.children:
                                if field.type == "field_declaration":
                                    fields_count += 1
                        structs.append(GoStructMetrics(
                            name=name,
                            lineno=node.start_point[0] + 1,
                            end_lineno=node.end_point[0] + 1,
                            num_fields=fields_count,
                            num_methods=0  # on compte les méthodes séparément
                        ))
            elif node.type == "import_declaration":
                imports += 1
            elif node.type == "import_spec":
                imports += 1
            
            for child in node.children:
                walk(child, struct_name)
        
        walk(root)
        
        return GoFileMetrics(
            path=filepath,
            num_imports=imports,
            functions=functions,
            structs=structs,
            num_lines=num_lines,
        )
    except Exception as e:
        return GoFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            structs=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_go_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers Go dans un répertoire."""
    all_files = []
    total_functions = 0
    total_structs = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target"}]
        for file in files:
            if file.endswith(".go"):
                full_path = os.path.join(root, file)
                metrics = _parse_go_file(full_path)
                all_files.append(metrics)
                total_functions += len(metrics.functions)
                total_structs += len(metrics.structs)
    
    return {
        "files_analyzed": len(all_files),
        "total_functions": total_functions,
        "total_structs": total_structs,
        "has_go_analysis": GO_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20]
    }