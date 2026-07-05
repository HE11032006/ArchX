"""
ruby_analyzer.py
------------------
Analyse les fichiers Ruby en utilisant tree-sitter-ruby
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    import tree_sitter_ruby as tsruby
    from tree_sitter import Language, Parser
    RUBY_AVAILABLE = True
except ImportError:
    RUBY_AVAILABLE = False

@dataclass
class RubyMethodMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_params: int
    class_name: str | None = None

@dataclass
class RubyClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int

@dataclass
class RubyFileMetrics:
    path: str
    num_imports: int
    methods: list[RubyMethodMetrics]
    classes: list[RubyClassMetrics]
    num_lines: int
    parse_error: str | None = None

def _count_branches_ruby(node) -> int:
    """Compte approximativement le nombre de branches dans un fichier Ruby."""
    count = 1
    if not RUBY_AVAILABLE:
        return 0
    
    for child in node.children:
        child_type = child.type
        if child_type in ["if", "unless", "while", "until", "for", "case", "when"]:
            count += 1
        count += _count_branches_ruby(child)
    return count

def _parse_ruby_file(filepath: str) -> RubyFileMetrics:
    """Analyse un fichier Ruby."""
    if not RUBY_AVAILABLE:
        return RubyFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=0,
            parse_error="tree-sitter-ruby non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return RubyFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        RUBY_LANGUAGE = Language(tsruby.language())
        parser = Parser(RUBY_LANGUAGE)
        tree = parser.parse(bytes(source, "utf-8"))
        root = tree.root_node
        
        methods = []
        classes = []
        imports = 0
        
        def walk(node, class_name: str | None = None):
            nonlocal imports
            if node.type == "method":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                params = 0
                param_node = node.child_by_field_name("parameters")
                if param_node:
                    for child in param_node.children:
                        if child.type == "parameter":
                            params += 1
                complexity = _count_branches_ruby(node)
                methods.append(RubyMethodMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    complexity=complexity,
                    num_params=params,
                    class_name=class_name
                ))
            elif node.type == "class":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else "anonymous"
                body = node.child_by_field_name("body")
                method_count = 0
                if body:
                    for child in body.children:
                        if child.type == "method":
                            method_count += 1
                classes.append(RubyClassMetrics(
                    name=name,
                    lineno=node.start_point[0] + 1,
                    end_lineno=node.end_point[0] + 1,
                    num_methods=method_count
                ))
                if body:
                    for child in body.children:
                        walk(child, name)
            elif node.type == "require":
                imports += 1
            elif node.type == "require_relative":
                imports += 1
            
            for child in node.children:
                walk(child, class_name)
        
        walk(root)
        
        return RubyFileMetrics(
            path=filepath,
            num_imports=imports,
            methods=methods,
            classes=classes,
            num_lines=num_lines,
        )
    except Exception as e:
        return RubyFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_ruby_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers Ruby dans un répertoire."""
    all_files = []
    total_methods = 0
    total_classes = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target"}]
        for file in files:
            if file.endswith(".rb"):
                full_path = os.path.join(root, file)
                metrics = _parse_ruby_file(full_path)
                all_files.append(metrics)
                total_methods += len(metrics.methods)
                total_classes += len(metrics.classes)
    
    return {
        "files_analyzed": len(all_files),
        "total_methods": total_methods,
        "total_classes": total_classes,
        "has_ruby_analysis": RUBY_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
        "files": all_files[:20]
    }