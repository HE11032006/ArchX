"""
coverage_estimate.py
----------------------
IMPORTANT : ceci est une ESTIMATION heuristique (ratio fonctions de test /
fonctions de code), pas une vraie couverture de lignes exécutées.

Pour une vraie mesure, il faut exécuter la suite de tests avec `coverage run`
puis `coverage json` — mais lancer une suite de tests arbitraire n'est pas
toujours sûr/possible en contexte automatisé (dépendances, DB, etc.).
Le nom du champ de sortie garde explicitement le suffixe "_estimate" pour ne
jamais laisser croire à un chiffre plus rigoureux qu'il ne l'est.
"""

from __future__ import annotations

from .complexity import FileMetrics

_TEST_FILE_HINTS = ("test_", "_test", "tests/", "/test/")


def is_test_file(path: str) -> bool:
    lower = path.lower()
    return any(hint in lower for hint in _TEST_FILE_HINTS)


def estimate_coverage(all_files: list[FileMetrics]) -> float:
    test_functions = 0
    source_functions = 0

    for f in all_files:
        if f.parse_error:
            continue
        if is_test_file(f.path):
            test_functions += len(f.functions)
        else:
            source_functions += len(f.functions)

    if source_functions == 0:
        return 0.0

    # Heuristique : ~1 test pour 1 fonction correspondrait à ~80% de couverture
    # dans la pratique courante ; on plafonne à 95 pour rester réaliste.
    ratio = test_functions / source_functions
    estimate = min(ratio * 80.0, 95.0)
    return round(estimate, 1)
