"""
complexity.py
--------------
Calcule la complexité cyclomatique et des métriques de taille par fonction/méthode
et par fichier, en utilisant uniquement le module `ast` de la bibliothèque standard
(aucune dépendance externe type radon/lizard requise).

Complexité cyclomatique = 1 + nombre de points de décision (if/for/while/except/
opérateurs booléens supplémentaires/comprehensions conditionnelles/assert/ternaires).
C'est l'algorithme standard de McCabe, le même que celui utilisé par radon en interne.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class FunctionMetrics:
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
class ClassMetrics:
    name: str
    lineno: int
    end_lineno: int
    num_methods: int
    num_lines: int
    method_names: list[str] = field(default_factory=list)


@dataclass
class FileMetrics:
    path: str
    num_imports: int
    imported_modules: list[str]
    functions: list[FunctionMetrics]
    classes: list[ClassMetrics]
    num_lines: int
    parse_error: str | None = None

    @property
    def avg_complexity(self) -> float:
        if not self.functions:
            return 0.0
        return sum(f.complexity for f in self.functions) / len(self.functions)

    @property
    def max_complexity(self) -> int:
        return max((f.complexity for f in self.functions), default=0)


class _ComplexityVisitor(ast.NodeVisitor):
    """Visite le corps d'UNE fonction et compte les points de décision."""

    def __init__(self) -> None:
        self.complexity = 1  # chemin de base

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:  # ternaire "a if cond else b"
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.complexity += len(node.items)
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # "a and b and c" = 2 points de décision supplémentaires (n-1 opérandes)
        self.complexity += max(len(node.values) - 1, 0)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.complexity += 1  # la boucle
        self.complexity += len(node.ifs)  # chaque "if" dans la comprehension
        self.generic_visit(node)


def _count_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    a = node.args
    return (
        len(a.posonlyargs)
        + len(a.args)
        + len(a.kwonlyargs)
        + (1 if a.vararg else 0)
        + (1 if a.kwarg else 0)
    )


def analyze_source(path: str, source: str) -> FileMetrics:
    """Analyse le code source d'un seul fichier Python et retourne ses métriques."""
    num_lines = source.count("\n") + 1
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return FileMetrics(
            path=path,
            num_imports=0,
            imported_modules=[],
            functions=[],
            classes=[],
            num_lines=num_lines,
            parse_error=f"SyntaxError: {exc}",
        )

    imported_modules: set[str] = set()
    functions: list[FunctionMetrics] = []
    classes: list[ClassMetrics] = []

    def _end_line(node: ast.AST, fallback: int) -> int:
        return getattr(node, "end_lineno", None) or fallback

    def _visit_function(node, class_name: str | None) -> FunctionMetrics:
        visitor = _ComplexityVisitor()
        for child in node.body:
            visitor.visit(child)
        end = _end_line(node, node.lineno)
        return FunctionMetrics(
            name=node.name,
            lineno=node.lineno,
            end_lineno=end,
            complexity=visitor.complexity,
            num_lines=end - node.lineno + 1,
            num_params=_count_params(node),
            class_name=class_name,
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".")[0])

    # Fonctions/méthodes top-level et de classe (on évite les doublons de fonctions
    # imbriquées en ne descendant pas dans les FunctionDef depuis ast.walk directement,
    # on les prend via un parcours explicite du corps des modules/classes).
    def _walk_body(body, class_name: str | None = None):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(_visit_function(node, class_name))
                _walk_body(node.body, class_name)  # fonctions imbriquées
            elif isinstance(node, ast.ClassDef):
                method_names = [
                    n.name
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                end = _end_line(node, node.lineno)
                classes.append(
                    ClassMetrics(
                        name=node.name,
                        lineno=node.lineno,
                        end_lineno=end,
                        num_methods=len(method_names),
                        num_lines=end - node.lineno + 1,
                        method_names=method_names,
                    )
                )
                _walk_body(node.body, node.name)
            elif hasattr(node, "body") and isinstance(getattr(node, "body"), list):
                # if/for/while/with/try au niveau module : on descend quand même
                # pour ne pas rater des fonctions définies dans un bloc conditionnel
                _walk_body(getattr(node, "body"), class_name)

    _walk_body(tree.body)

    return FileMetrics(
        path=path,
        num_imports=len(imported_modules),
        imported_modules=sorted(imported_modules),
        functions=functions,
        classes=classes,
        num_lines=num_lines,
    )


def analyze_file(path: str) -> FileMetrics:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    return analyze_source(path, source)
