"""
architecture.py
-----------------
Détecte le pattern architectural probable d'un projet à partir de signaux
structurels objectifs (noms de dossiers/fichiers présents), plutôt que de
demander à un LLM de "deviner" sans preuve.

C'est une heuristique de premier niveau : le rôle du modèle fine-tuné est
ensuite d'affiner/nuancer ce diagnostic dans le champ "analysis", pas de
recalculer ce qui est déjà déterministe.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ArchitectureSignal:
    pattern: str
    confidence: str  # "low" | "medium" | "high"
    evidence: list[str]


# (nom_de_dossier_ou_fichier_en_minuscule, poids)
_SIGNATURES: dict[str, list[str]] = {
    "Django (MVT)": ["manage.py", "settings.py", "wsgi.py", "urls.py"],
    "Flask (monolithe léger)": ["app.py", "wsgi.py"],
    "Hexagonal / Clean Architecture": [
        "domain", "application", "infrastructure", "adapters", "ports", "usecases",
    ],
    "MVC classique": ["models", "views", "controllers", "templates"],
    "Microservices": ["services", "docker-compose.yml", "k8s", "helm"],
    "Layered (N-tiers)": ["dal", "bll", "presentation", "repository", "repositories"],
}


def detect_architecture(repo_path: str) -> ArchitectureSignal:
    found: dict[str, list[str]] = {}

    for root, dirs, files in os.walk(repo_path):
        # ignore les dossiers bruyants
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__"}]
        names_lower = {d.lower() for d in dirs} | {f.lower() for f in files}
        for pattern, signals in _SIGNATURES.items():
            hits = names_lower & {s.lower() for s in signals}
            if hits:
                found.setdefault(pattern, [])
                for h in hits:
                    rel = os.path.relpath(root, repo_path)
                    evidence = f"{rel}/{h}" if rel != "." else h
                    if evidence not in found[pattern]:
                        found[pattern].append(evidence)

    if not found:
        return ArchitectureSignal(
            pattern="Non déterminé (structure ad-hoc / script unique)",
            confidence="low",
            evidence=[],
        )

    # le pattern avec le plus d'indices distincts gagne
    best_pattern = max(found, key=lambda p: len(found[p]))
    n_evidence = len(found[best_pattern])
    confidence = "high" if n_evidence >= 3 else "medium" if n_evidence == 2 else "low"

    return ArchitectureSignal(
        pattern=best_pattern,
        confidence=confidence,
        evidence=found[best_pattern],
    )
