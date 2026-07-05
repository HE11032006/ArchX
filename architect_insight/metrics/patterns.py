"""
patterns.py
------------
Détecte des anti-patterns objectifs à partir des métriques extraites par
complexity.py. Chaque règle est un seuil documenté et modifiable — l'idée
n'est pas de "deviner" via un LLM mais de calculer des faits vérifiables.

Seuils par défaut inspirés de la littérature courante (Fowler, Lanza & Marinescu
"Object-Oriented Metrics in Practice") — à ajuster selon le langage/l'équipe.
"""

from __future__ import annotations

from dataclasses import dataclass

from .complexity import FileMetrics


@dataclass
class AntiPattern:
    type: str
    location: str
    severity: str  # "low" | "medium" | "high"
    detail: str

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "location": self.location,
            "severity": self.severity,
            "detail": self.detail,
        }


# Seuils (modifiables)
GOD_CLASS_METHODS = 15
GOD_CLASS_LINES = 300
LONG_METHOD_LINES = 60
LONG_METHOD_COMPLEXITY = 10
LONG_PARAMETER_LIST = 6
HIGH_COUPLING_IMPORTS = 20


def detect_anti_patterns(file_metrics: FileMetrics) -> list[AntiPattern]:
    findings: list[AntiPattern] = []

    for cls in file_metrics.classes:
        if cls.num_methods >= GOD_CLASS_METHODS or cls.num_lines >= GOD_CLASS_LINES:
            severity = "high" if cls.num_methods >= GOD_CLASS_METHODS * 1.5 else "medium"
            findings.append(
                AntiPattern(
                    type="God Class",
                    location=f"{file_metrics.path}:{cls.name} (L{cls.lineno})",
                    severity=severity,
                    detail=(
                        f"{cls.num_methods} méthodes, {cls.num_lines} lignes "
                        f"(seuils: {GOD_CLASS_METHODS} méthodes / {GOD_CLASS_LINES} lignes)"
                    ),
                )
            )

    for fn in file_metrics.functions:
        if fn.num_lines >= LONG_METHOD_LINES or fn.complexity >= LONG_METHOD_COMPLEXITY:
            severity = "high" if fn.complexity >= LONG_METHOD_COMPLEXITY * 2 else "medium"
            findings.append(
                AntiPattern(
                    type="Long Method",
                    location=f"{file_metrics.path}:{fn.qualified_name} (L{fn.lineno})",
                    severity=severity,
                    detail=(
                        f"{fn.num_lines} lignes, complexité cyclomatique {fn.complexity} "
                        f"(seuils: {LONG_METHOD_LINES} lignes / {LONG_METHOD_COMPLEXITY})"
                    ),
                )
            )

        if fn.num_params >= LONG_PARAMETER_LIST:
            findings.append(
                AntiPattern(
                    type="Long Parameter List",
                    location=f"{file_metrics.path}:{fn.qualified_name} (L{fn.lineno})",
                    severity="medium",
                    detail=f"{fn.num_params} paramètres (seuil: {LONG_PARAMETER_LIST})",
                )
            )

    if file_metrics.num_imports >= HIGH_COUPLING_IMPORTS:
        findings.append(
            AntiPattern(
                type="High Coupling (fichier)",
                location=file_metrics.path,
                severity="medium",
                detail=(
                    f"{file_metrics.num_imports} modules importés distincts "
                    f"(seuil: {HIGH_COUPLING_IMPORTS})"
                ),
            )
        )

    if file_metrics.parse_error:
        findings.append(
            AntiPattern(
                type="Fichier non analysable",
                location=file_metrics.path,
                severity="low",
                detail=file_metrics.parse_error,
            )
        )

    return findings


def coupling_score(all_files: list[FileMetrics]) -> float:
    """Score de couplage /10 basé sur la moyenne d'imports par fichier,
    normalisé contre le seuil HIGH_COUPLING_IMPORTS (=8/10)."""
    files_with_code = [f for f in all_files if not f.parse_error]
    if not files_with_code:
        return 0.0
    avg_imports = sum(f.num_imports for f in files_with_code) / len(files_with_code)
    score = (avg_imports / HIGH_COUPLING_IMPORTS) * 8.0
    return round(min(score, 10.0), 1)


def cohesion_score(all_files: list[FileMetrics]) -> float:
    """Proxy de cohésion /10 : les classes avec peu de méthodes et une taille
    raisonnable sont considérées plus cohésives (heuristique volontairement
    simple — une vraie mesure LCOM nécessiterait d'analyser quels attributs
    chaque méthode utilise réellement, cf. limites documentées dans le README)."""
    all_classes = [c for f in all_files for c in f.classes]
    if not all_classes:
        return 5.0  # valeur neutre si pas de classes (code procédural)
    penalties = [
        1.0 if (c.num_methods >= GOD_CLASS_METHODS or c.num_lines >= GOD_CLASS_LINES) else 0.0
        for c in all_classes
    ]
    ratio_healthy = 1 - (sum(penalties) / len(all_classes))
    return round(3.0 + ratio_healthy * 7.0, 1)
