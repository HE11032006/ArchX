"""
collector.py
--------------
Point d'entrée principal. Parcourt un dépôt, calcule toutes les métriques
RÉELLES (pas de génération LLM ici), et produit un JSON prêt à être injecté
dans le prompt du modèle Gemma fine-tuné, qui lui se charge uniquement du
raisonnement/synthèse/recommandation — jamais des chiffres bruts.

Usage :
    python -m architect_insight.collector /chemin/vers/le/repo -o rapport.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .metrics.architecture import detect_architecture
from .metrics.complexity import FileMetrics, analyze_source
from .metrics.coverage_estimate import estimate_coverage
from .metrics.git_hotspots import analyze_hotspots
from .metrics.patterns import cohesion_score, coupling_score, detect_anti_patterns
from .metrics.dependencies import analyze_dependencies
from .metrics.databases import detect_database
from .metrics.tests import analyze_tests
from .metrics.performance import detect_performance
from .analyzers.js_analyzer import analyze_js_directory
from .analyzers.java_analyzer import analyze_java_directory
from .analyzers.dart_analyzer import analyze_dart_directory
from .analyzers.go_analyzer import analyze_go_directory
from .analyzers.rust_analyzer import analyze_rust_directory
from .analyzers.ruby_analyzer import analyze_ruby_directory
from .analyzers.php_analyzer import analyze_php_directory
from .analyzers.cs_analyzer import analyze_cs_directory
from .analyzers.cpp_analyzer import analyze_cpp_directory

_IGNORED_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".mypy_cache"}


def _iter_python_files(repo_path: str):
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS]
        for fname in files:
            if fname.endswith(".py"):
                full = os.path.join(root, fname)
                yield full


def collect(repo_path: str) -> dict:
    repo_path = os.path.abspath(repo_path)
    all_files: list[FileMetrics] = []

    for full_path in _iter_python_files(repo_path):
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except OSError as exc:
            continue
        rel_path = os.path.relpath(full_path, repo_path)
        all_files.append(analyze_source(rel_path, source))

    # Calculé avant le bloc anti_patterns pour pouvoir y fusionner les
    # anti-patterns Java (detect_anti_patterns est full duck-typed : les
    # dataclasses de java_analyzer.py reprennent exactement la forme de
    # FileMetrics/FunctionMetrics/ClassMetrics, aucune adaptation nécessaire).
    java_metrics = analyze_java_directory(repo_path)

    anti_patterns = []
    for fm in all_files:
        anti_patterns.extend(p.to_dict() for p in detect_anti_patterns(fm))
    # "files" contient des dataclasses JavaFileMetrics (pas JSON-serializable) —
    # utilisées ici uniquement pour la fusion des anti-patterns, puis retirées
    # avant que java_metrics parte dans le rapport final (voir plus bas).
    for java_fm in java_metrics.pop("files", []):
        anti_patterns.extend(p.to_dict() for p in detect_anti_patterns(java_fm))

    # tri par sévérité pour mettre les plus critiques en premier
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    anti_patterns.sort(key=lambda p: severity_rank.get(p["severity"], 3))

    architecture = detect_architecture(repo_path)
    hotspots = analyze_hotspots(repo_path)

    complexity_hotspots = sorted(
        (fm for fm in all_files if not fm.parse_error and fm.functions),
        key=lambda fm: fm.max_complexity,
        reverse=True,
    )[:10]

    total_functions = sum(len(fm.functions) for fm in all_files)
    total_classes = sum(len(fm.classes) for fm in all_files)
    avg_complexity_overall = (
        round(sum(fm.avg_complexity * len(fm.functions) for fm in all_files) / total_functions, 2)
        if total_functions
        else 0.0
    )

    dependencies = analyze_dependencies(repo_path)
    database = detect_database(repo_path)
    tests = analyze_tests(repo_path)
    performance = detect_performance(repo_path)
    # Analyse multi-langages avancée (AST)
    js_metrics = analyze_js_directory(repo_path)
    # java_metrics déjà calculé plus haut (nécessaire avant le bloc anti_patterns)
    dart_metrics = analyze_dart_directory(repo_path)
    # Analyse AST multi-langages (nouveaux)
    go_metrics = analyze_go_directory(repo_path)
    rust_metrics = analyze_rust_directory(repo_path)
    ruby_metrics = analyze_ruby_directory(repo_path)
    php_metrics = analyze_php_directory(repo_path)
    cs_metrics = analyze_cs_directory(repo_path)
    cpp_metrics = analyze_cpp_directory(repo_path)

    return {
        "repo_path": repo_path,
        "files_analyzed": len(all_files),
        "files_with_errors": sum(1 for fm in all_files if fm.parse_error),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "architecture_pattern": architecture.pattern,
        "architecture_confidence": architecture.confidence,
        "architecture_evidence": architecture.evidence,
        "coupling_score": coupling_score(all_files),
        "cohesion_score": cohesion_score(all_files),
        "avg_cyclomatic_complexity": avg_complexity_overall,
        "test_coverage_estimate": estimate_coverage(all_files),
        "anti_patterns": anti_patterns[:20],
        "complexity_hotspots": [
            {
                "file": fm.path,
                "max_complexity": fm.max_complexity,
                "num_functions": len(fm.functions),
                "num_lines": fm.num_lines,
                "num_imports": fm.num_imports,
            }
            for fm in complexity_hotspots
        ],
        "git_hotspots": [
            {
                "file": h.path,
                "total_changes_12mo": h.total_changes,
                "bugfix_changes_12mo": h.bugfix_changes,
                "bugfix_ratio": h.bugfix_ratio,
            }
            for h in hotspots
        ],
        "top_hotspot_bugfix_ratio": extract_top_hotspot_metrics(
            [{"bugfix_ratio": h.bugfix_ratio} for h in hotspots]
        )["top_hotspot_bugfix_ratio"],
        "num_hotspots": len(hotspots),
        "dependencies": dependencies,
        "database": database,
        "tests": tests,
        "performance": performance,
        "js_analysis": js_metrics,
        "java_analysis": java_metrics,
        "dart_analysis": dart_metrics,
        "go_analysis": go_metrics,
        "rust_analysis": rust_metrics,
        "ruby_analysis": ruby_metrics,
        "php_analysis": php_metrics,
        "cs_analysis": cs_metrics,
        "cpp_analysis": cpp_metrics,
    }

# Dans collector.py, après la définition de collect(), ajoute :

def extract_top_hotspot_metrics(hotspots: list[dict]) -> dict:
    """
    Extrait les métriques agrégées des hotspots Git pour correspondre
    au format attendu par le modèle (entraîné sur des scénarios synthétiques).
    """
    if not hotspots:
        return {
            "top_hotspot_bugfix_ratio": 0.0,
            "num_hotspots": 0,
            "avg_bugfix_ratio": 0.0,
        }
    
    ratios = [h["bugfix_ratio"] for h in hotspots]
    return {
        "top_hotspot_bugfix_ratio": max(ratios),
        "num_hotspots": len(hotspots),
        "avg_bugfix_ratio": round(sum(ratios) / len(ratios), 2),
    }





def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collecte des métriques RÉELLES d'un repo Python (aucune IA impliquée)."
    )
    parser.add_argument("repo_path", help="Chemin vers le dépôt à analyser")
    parser.add_argument("-o", "--output", help="Fichier JSON de sortie (sinon stdout)")
    args = parser.parse_args()

    if not os.path.isdir(args.repo_path):
        print(f"Erreur : {args.repo_path} n'est pas un dossier valide", file=sys.stderr)
        sys.exit(1)

    report = collect(args.repo_path)
    output = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Rapport écrit dans {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
