"""
java_analyzer.py
------------------
Analyse les fichiers Java en utilisant javaparser
pour extraire des métriques de base.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from javaparser import JavaParser
    JAVA_AVAILABLE = True
except ImportError:
    JAVA_AVAILABLE = False

@dataclass
class JavaMethodMetrics:
    name: str
    lineno: int
    end_lineno: int
    complexity: int
    num_params: int
    class_name: str | None = None

@dataclass
class JavaClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int

@dataclass
class JavaFileMetrics:
    path: str
    num_imports: int
    methods: list[JavaMethodMetrics]
    classes: list[JavaClassMetrics]
    num_lines: int
    parse_error: str | None = None

def _parse_java_file(filepath: str) -> JavaFileMetrics:
    """Analyse un fichier Java."""
    if not JAVA_AVAILABLE:
        return JavaFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=0,
            parse_error="javaparser non installé"
        )
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        return JavaFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=0,
            parse_error=f"Erreur de lecture: {e}"
        )
    
    num_lines = source.count("\n") + 1
    
    try:
        parser = JavaParser()
        tree = parser.parse(source)
        
        methods = []
        classes = []
        imports = 0
        
        # Parcourir l'AST Java
        for node in tree.walk():
            node_type = str(node.__class__.__name__)
            
            if "ImportDeclaration" in node_type:
                imports += 1
            elif "ClassDeclaration" in node_type:
                name = getattr(node, "name", {}).get("identifier", "anonymous")
                methods_count = 0
                # Compter les méthodes
                for child in node.walk():
                    if "MethodDeclaration" in str(child.__class__.__name__):
                        methods_count += 1
                classes.append(JavaClassMetrics(
                    name=name,
                    lineno=getattr(node, "range", {}).get("begin", {}).get("line", 0),
                    end_lineno=getattr(node, "range", {}).get("end", {}).get("line", 0),
                    num_methods=methods_count
                ))
            elif "MethodDeclaration" in node_type:
                name = getattr(node, "name", {}).get("identifier", "anonymous")
                params = getattr(node, "parameters", [])
                methods.append(JavaMethodMetrics(
                    name=name,
                    lineno=getattr(node, "range", {}).get("begin", {}).get("line", 0),
                    end_lineno=getattr(node, "range", {}).get("end", {}).get("line", 0),
                    complexity=1,  # Approximation simple
                    num_params=len(params),
                    class_name=None
                ))
        
        return JavaFileMetrics(
            path=filepath,
            num_imports=imports,
            methods=methods,
            classes=classes,
            num_lines=num_lines,
        )
    except Exception as e:
        return JavaFileMetrics(
            path=filepath,
            num_imports=0,
            methods=[],
            classes=[],
            num_lines=num_lines,
            parse_error=f"Erreur de parsing: {e}"
        )

def analyze_java_directory(repo_path: str) -> dict:
    """Analyse tous les fichiers Java dans un répertoire."""
    all_files = []
    total_methods = 0
    total_classes = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target", "build"}]
        for file in files:
            if file.endswith(".java"):
                full_path = os.path.join(root, file)
                metrics = _parse_java_file(full_path)
                all_files.append(metrics)
                total_methods += len(metrics.methods)
                total_classes += len(metrics.classes)
    
    return {
        "files_analyzed": len(all_files),
        "total_methods": total_methods,
        "total_classes": total_classes,
        "has_java_analysis": JAVA_AVAILABLE,
        "file_errors": sum(1 for f in all_files if f.parse_error),
    }