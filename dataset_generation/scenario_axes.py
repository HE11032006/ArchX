"""
scenario_axes.py
------------------
Définit les axes de variation d'un scénario de projet ET les échantillonne
par script — le modèle enseignant ne fait QUE rédiger, il n'invente pas la
combinaison. C'est ce qui évite la répétitivité (mode collapse) qu'on aurait
avec un simple prompt "génère 500 descriptions variées".

Point clé anti-biais : les métriques sont tirées dans 3 "bandes de santé"
(healthy / moderate / critical) réparties volontairement (30/40/30 par défaut).
Ça garantit que le dataset contient de vrais cas où la bonne réponse d'un
architecte senior est "ne migre pas" — sinon le modèle fine-tuné apprend un
réflexe de rewrite systématique, qui est exactement l'anti-pattern qu'un vrai
architecte évite.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict

SECTORS = [
    "fintech / paiements",
    "e-commerce",
    "SaaS B2B (gestion d'entreprise)",
    "IoT industriel",
    "santé / medtech",
    "logistique / supply chain",
    "media / streaming",
    "gaming",
    "edtech",
    "marketplace",
]

STACKS = [
    ("Python", "Django", "PostgreSQL"),
    ("Python", "Flask", "PostgreSQL"),
    ("Python", "FastAPI", "PostgreSQL"),
    ("Ruby", "Rails", "MySQL"),
    ("PHP", "Laravel", "MySQL"),
    ("Node.js", "Express", "MongoDB"),
    ("Java", "Spring Boot", "PostgreSQL"),
    (".NET", "ASP.NET Core", "SQL Server"),
    ("Python", "Django", "MongoDB"),
    ("Node.js", "NestJS", "PostgreSQL"),
]

DOMINANT_CONSTRAINTS = [
    "scalabilité (pics de trafic imprévisibles)",
    "coût cloud qui dérape",
    "vélocité de développement (features trop lentes à livrer)",
    "conformité réglementaire (RGPD, PCI-DSS, HDS...)",
    "fiabilité / uptime (incidents en prod trop fréquents)",
    "pénurie de talents sur la stack actuelle",
    "latence temps réel critique",
    "aucune contrainte critique identifiée pour l'instant",
]

ANTI_PATTERN_TYPES = [
    "God Class", "Long Method", "Long Parameter List",
    "High Coupling", "Duplicate Code", "Circular Dependency",
]

# (coupling, cohesion, coverage%, avg_complexity, bugfix_ratio_top_hotspot, nb_anti_patterns)
HEALTH_BANDS = {
    "healthy":  {"coupling": (1, 3),  "cohesion": (7, 10), "coverage": (60, 90), "complexity": (1, 4),  "bugfix_ratio": (0.0, 0.2), "anti_patterns": (0, 1)},
    "moderate": {"coupling": (3, 6),  "cohesion": (4, 7),  "coverage": (30, 60), "complexity": (4, 7),  "bugfix_ratio": (0.2, 0.5), "anti_patterns": (2, 5)},
    "critical": {"coupling": (6, 10), "cohesion": (1, 4),  "coverage": (5, 30),  "complexity": (7, 12), "bugfix_ratio": (0.5, 0.9), "anti_patterns": (5, 12)},
}

HEALTH_BAND_WEIGHTS = {"healthy": 0.30, "moderate": 0.40, "critical": 0.30}


@dataclass
class Scenario:
    scenario_id: str
    sector: str
    team_size: int
    pct_junior: int
    pct_senior: int
    codebase_age_years: float
    language: str
    framework: str
    database: str
    dominant_constraint: str
    health_band: str
    metrics: dict = field(default_factory=dict)
    anti_patterns: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _sample_metrics(rng: random.Random, band: str) -> dict:
    b = HEALTH_BANDS[band]
    return {
        "coupling_score": round(rng.uniform(*b["coupling"]), 1),
        "cohesion_score": round(rng.uniform(*b["cohesion"]), 1),
        "test_coverage_estimate": round(rng.uniform(*b["coverage"]), 1),
        "avg_cyclomatic_complexity": round(rng.uniform(*b["complexity"]), 1),
        "top_hotspot_bugfix_ratio": round(rng.uniform(*b["bugfix_ratio"]), 2),
    }


def _sample_anti_patterns(rng: random.Random, band: str, module_hint: str) -> list[dict]:
    lo, hi = HEALTH_BANDS[band]["anti_patterns"]
    n = rng.randint(lo, hi)
    picks = []
    for _ in range(n):
        picks.append({
            "type": rng.choice(ANTI_PATTERN_TYPES),
            "location": f"src/{module_hint}/{rng.choice(['core', 'service', 'handler', 'processor'])}.py",
            "severity": rng.choice(["medium", "high"]) if band != "healthy" else "low",
        })
    return picks


def sample_scenarios(n: int, seed: int = 42) -> list[Scenario]:
    rng = random.Random(seed)
    seen: set[tuple] = set()
    scenarios: list[Scenario] = []
    bands = list(HEALTH_BAND_WEIGHTS.keys())
    weights = list(HEALTH_BAND_WEIGHTS.values())

    attempts = 0
    while len(scenarios) < n and attempts < n * 20:
        attempts += 1
        sector = rng.choice(SECTORS)
        stack = rng.choice(STACKS)
        constraint = rng.choice(DOMINANT_CONSTRAINTS)
        band = rng.choices(bands, weights=weights, k=1)[0]

        key = (sector, stack, constraint, band)
        if key in seen:
            continue  # évite les doublons catégoriels exacts
        seen.add(key)

        team_size = rng.randint(3, 45)
        pct_junior = rng.randint(10, 80)
        pct_senior = rng.randint(5, min(90, 100 - pct_junior))

        module_hint = sector.split(" ")[0].split("/")[0].strip().lower().replace("é", "e")

        scenario = Scenario(
            scenario_id=f"scn_{len(scenarios):04d}",
            sector=sector,
            team_size=team_size,
            pct_junior=pct_junior,
            pct_senior=pct_senior,
            codebase_age_years=round(rng.uniform(0.5, 15), 1),
            language=stack[0],
            framework=stack[1],
            database=stack[2],
            dominant_constraint=constraint,
            health_band=band,
            metrics=_sample_metrics(rng, band),
            anti_patterns=_sample_anti_patterns(rng, band, module_hint),
        )
        scenarios.append(scenario)

    return scenarios


if __name__ == "__main__":
    import json
    from collections import Counter

    sample = sample_scenarios(400)
    band_counts = Counter(s.health_band for s in sample)
    print(f"Généré {len(sample)} scénarios uniques")
    print(f"Répartition des bandes de santé : {dict(band_counts)}")
    print("\nExemple (bande 'critical') :")
    critical_example = next(s for s in sample if s.health_band == "critical")
    print(json.dumps(critical_example.to_dict(), indent=2, ensure_ascii=False))
    print("\nExemple (bande 'healthy') :")
    healthy_example = next(s for s in sample if s.health_band == "healthy")
    print(json.dumps(healthy_example.to_dict(), indent=2, ensure_ascii=False))
