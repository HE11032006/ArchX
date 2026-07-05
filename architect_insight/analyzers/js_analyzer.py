"""
js_analyzer.py
----------------
Analyse les fichiers JavaScript/TypeScript en utilisant tree-sitter
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    import tree_sitter_javascript as tsjs
    from tree_sitter import Language, Parser
    JS_AVAILABLE = True
except ImportError:
    JS_AVAILABLE = False

@dataclass
class JSFunctionMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int  # approximation (nombre de branches)
    num_params: int
    class_name: str | None = None

@dataclass
class JSClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int

@dataclass
class JSFileMetrics:
    path: str
    num_imports: int
    functions: list[JSFunctionMetrics]
    classes: list[JSClassMetrics]
    num_lines: int
    parse_error: str | None = None

def _count_branches(node) -> int:
    """Compte approximativement le nombre de branches (complexité)."""
    count = 1  # chemin de base
    if not JS_AVAILABLE:
        return 0
    
    # Parcourir l'arbre pour trouver les points de décision
    for child in node.children:
        child_type = child.type
        if child_type in ["if_statement", "for_statement", "while_statement", 
                          "do_statement", "switch_statement", "conditional_expression",
                          "catch_clause"]:
            count += 1
        # Opérateurs booléens
        if child_type == "binary_expression":
            if child.text and b"&&" in child.text or b"||" in child.text:
                count += 1
        count += _count_branches(child)
    return count

def _parse_js_file(filepath: str) -> JSFileMetrics:
    """Analyse un fichier JavaScript/TypeScript."""
    if not JS_AVAILABLE:
        return JSFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=0,
            parse_error="tree-sitter-javascript non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return JSFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        # Initialiser le parser
        JS_LANGUAGE = Language(tsjs.language())
        parser = Parser(JS_LANGUAGE)
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
                params = len(node.children_by_field_name("parameters"))
                complexity = _count_branches(node)
                functions.append(JSFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    class_name=class_name
                ))
            elif node.type == "method_definition":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                complexity = _count_branches(node)
                functions.append(JSFunctionMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    class_name=class_name
                ))
            elif node.type == "arrow_function":
                # Les fonctions fléchées
                params = 0
                complexity = _count_branches(node)
                functions.append(JSFunctionMetrics(
                    name="arrow_function",
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
                        if child.type in ["method_definition", "field_definition"]:
                            method_count += 1
                classes.append(JSClassMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    num_methods=method_count
                ))
                # Analyser les méthodes de la classe
                if class_body:
                    for child in class_body.children:
                        walk(child, name)
            elif node.type == "import_statement":
                imports += 1
            elif node.type == "import":
                imports += 1
            
            for child in node.children:
                if child.type not in ["class_declaration", "function_declaration", "method_definition"]:
                    walk(child, class_name)
        
        walk(root)
        
        return JSFileMetrics(
            path=filepath,
            num_imports=imports,
            functions=functions,
            classes=classes,
            num_lines=num_lines,
        )
    except Exception as e:
        return JSFileMetrics(
            path=filepath,
            num_imports=0,
            functions=[],
            classes=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_js_directory(repo_path: str, extensions: list[str] = None) -> dict:
    """Analyse tous les fichiers JS/TS dans un répertoire."""
    if extensions is None:
        extensions = [".js", ".ts", ".jsx", ".tsx"]
    
    all_files = []
    total_functions = 0
    total_classes = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions:
                full_path = os.path.join(root, file)
                metrics = _parse_js_file(full_path)
                all_files.append(metrics)
                total_functions += len(metrics.functions)
                total_classes += len(metrics.classes)
    
    return {
        "files_analyzed": len(all_files),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "has_js_analysis": JS_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20]  # Limite pour ne pas surcharger
    }