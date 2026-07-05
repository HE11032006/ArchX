"""
tests.py
----------
Analyse les tests d'un projet :
- Nombre de fichiers de test
- Nombre de fonctions de test
- Types de tests (unitaires, intégration, end-to-end)
- Framework de test utilisé
- Estimation du ratio de tests
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

# Frameworks de test par langage
TEST_FRAMEWORKS = {
    "pytest": ["pytest", "test_", "_test.py"],
    "unittest": ["unittest", "TestCase"],
    "jest": ["jest", "test.js", "spec.js"],
    "mocha": ["mocha", "test.js", "spec.js"],
    "junit": ["junit", "@Test"],
    "testng": ["testng", "@Test"],
    "flutter_test": ["flutter_test", "test/widget_test"],
    "go_test": ["_test.go"],
    "cargo_test": ["cargo test"],
    "rspec": ["rspec", "_spec.rb"],
}

TEST_TYPE_PATTERNS = {
    "unit": ["test_unit", "unit_test", "spec"],
    "integration": ["test_integration", "integration_test", "it_test", "test/integration"],
    "e2e": ["test_e2e", "e2e", "cypress", "playwright"],
    "widget": ["widget_test", "golden_test"],
}


def analyze_tests(repo_path: str) -> dict:
    """
    Analyse les tests dans le dépôt.
    """
    repo_path = os.path.abspath(repo_path)
    test_files = []
    test_functions = []
    detected_frameworks = set()
    test_types = {"unit": 0, "integration": 0, "e2e": 0, "widget": 0, "other": 0}
    
    for root, dirs, files in os.walk(repo_path):
        # Ignorer les dossiers inutiles
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target"}]
        
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, repo_path)
            
            # Détection des frameworks
            for framework, patterns in TEST_FRAMEWORKS.items():
                for pattern in patterns:
                    if pattern in rel_path.lower() or pattern in file.lower():
                        detected_frameworks.add(framework)
            
            # Détection des fichiers de test
            is_test_file = False
            for pattern in ["test_", "_test.", ".test.", "spec.", "tests/", "test/", "__tests__"]:
                if pattern in rel_path.lower():
                    is_test_file = True
                    break
            
            if is_test_file:
                test_files.append(rel_path)
                
                # Compter les fonctions de test dans le fichier
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # Patterns communs pour les fonctions de test
                        count = len(re.findall(r'(?i)(def test_|test\s*\(|it\s*\(|test\s*:|@Test|await.*\.test)', content))
                        test_functions.append({"file": rel_path, "count": count})
                except Exception:
                    test_functions.append({"file": rel_path, "count": 1})
                
                # Détection du type de test
                for test_type, patterns in TEST_TYPE_PATTERNS.items():
                    for pattern in patterns:
                        if pattern in rel_path.lower():
                            test_types[test_type] += 1
                            break
                else:
                    test_types["other"] += 1
    
    total_test_functions = sum(t["count"] for t in test_functions)
    total_test_files = len(test_files)
    
    # Estimer le ratio de tests (par rapport au nombre total de fichiers)
    total_files = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target"}]
        total_files += len([f for f in files if f.endswith((".py", ".js", ".ts", ".java", ".dart", ".go", ".rs"))])
    
    test_ratio = round((total_test_files / total_files) * 100, 1) if total_files > 0 else 0.0
    
    # Estimation de la couverture (proxy basé sur le ratio de tests)
    if test_ratio > 40:
        coverage_estimate = "high"
    elif test_ratio > 20:
        coverage_estimate = "medium"
    elif test_ratio > 5:
        coverage_estimate = "low"
    else:
        coverage_estimate = "very_low"
    
    return {
        "total_test_files": total_test_files,
        "total_test_functions": total_test_functions,
        "test_ratio": test_ratio,
        "coverage_estimate": coverage_estimate,
        "frameworks": list(detected_frameworks) if detected_frameworks else ["Non détecté"],
        "test_types": test_types,
        "top_test_files": [t["file"] for t in test_functions[:10]],
    }