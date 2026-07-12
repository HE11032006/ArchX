"""
cost_calculator.py
-------------------
Calcule les coûts réels et le ROI à partir des métriques collectées et de la
recommandation du modèle. Tous les chiffres sont calculés par des formules
déterministes, jamais générés par un LLM.

Ce module est appelé APRÈS que le modèle a produit sa recommandation, pour
ajouter les données financières au rapport final.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Coûts mensuels estimés (€) pour une charge "medium" (~500 req/sec).
# Basé sur des données publiques (TechEmpower, grilles tarifaires AWS/Azure/GCP).
# Module-level (pas local à estimate_cloud_cost_from_stack) pour être réutilisable
# ailleurs (ex: liste des stacks disponibles pour le simulateur de migration).
STACK_MONTHLY_COSTS: dict[str, float] = {
    "Django": 2450,
    "Flask": 2100,
    "FastAPI": 1800,
    "Go": 1200,
    "Rust": 800,
    "Node.js": 1600,
    "Spring Boot": 2800,
    "Laravel": 2300,
    "Rails": 2200,
    "ASP.NET Core": 2500,
}

# Suggestions de cibles de migration "typiques" par stack actuelle — heuristique
# simple, pas une vérité absolue. Sert de point de départ raisonnable au
# simulateur de migration, pas une recommandation définitive.
DEFAULT_MIGRATION_SUGGESTIONS: dict[str, list[str]] = {
    "Django": ["FastAPI", "Go"],
    "Flask": ["FastAPI", "Go"],
    "FastAPI": ["Go"],
    "Ruby": [],
    "Rails": ["Go", "Node.js"],
    "PHP": [],
    "Laravel": ["Node.js", "Go"],
    "Node.js": ["Go"],
    "Java": [],
    "Spring Boot": ["Go", "FastAPI"],
    ".NET": [],
    "ASP.NET Core": ["Go", "FastAPI"],
    "Go": [],
    "Rust": [],
}


@dataclass
class CostReport:
    """Rapport financier complet."""
    migration_cost: float           # Coût total de la migration (€)
    current_cloud_cost: float       # Coût cloud actuel (€/mois)
    target_cloud_cost: float        # Coût cloud cible (€/mois)
    monthly_savings: float          # Économie mensuelle (€)
    roi_months: float               # Retour sur investissement (mois)
    payback_months: float           # Remboursement (mois)
    cost_confidence: str            # "high", "medium", "low"


def calculate_migration_cost(
    duration_days: int,
    team_size: int,
    hourly_rate: float = 80.0,
) -> float:
    """
    Calcule le coût total de la migration.
    
    Args:
        duration_days: Durée estimée en jours (venant du modèle)
        team_size: Taille recommandée de l'équipe (venant du modèle)
        hourly_rate: Taux horaire moyen d'un développeur (défaut: 80€)
    
    Returns:
        Coût total en euros
    """
    total_hours = duration_days * 8 * team_size
    return round(total_hours * hourly_rate, 2)


def calculate_cloud_cost_delta(
    current_monthly_cost: float,
    target_monthly_cost: float,
) -> tuple[float, float]:
    """
    Calcule les économies mensuelles et l'écart.
    
    Args:
        current_monthly_cost: Coût cloud actuel (€/mois)
        target_monthly_cost: Coût cloud estimé après migration (€/mois)
    
    Returns:
        (monthly_savings, delta) : économies et écart en pourcentage
    """
    monthly_savings = round(current_monthly_cost - target_monthly_cost, 2)
    if current_monthly_cost > 0:
        delta_pct = round((monthly_savings / current_monthly_cost) * 100, 1)
    else:
        delta_pct = 0.0
    return monthly_savings, delta_pct


def calculate_roi(
    migration_cost: float,
    monthly_savings: float,
) -> float:
    """
    Calcule le retour sur investissement en mois.
    
    Args:
        migration_cost: Coût total de la migration (€)
        monthly_savings: Économies mensuelles (€/mois)
    
    Returns:
        ROI en mois (arrondi à 1 décimale)
    """
    if monthly_savings <= 0:
        return float('inf')
    return round(migration_cost / monthly_savings, 1)


def estimate_cloud_cost_from_stack(stack_name: str, scale: str = "medium") -> float:
    """
    Estime le coût cloud mensuel pour une stack donnée.
    Basé sur des données publiques (TechEmpower, grilles tarifaires AWS/Azure/GCP).
    
    Args:
        stack_name: Nom de la stack (ex: "Django", "Go", "Rust", "FastAPI")
        scale: Niveau de charge ("small", "medium", "large")
    
    Returns:
        Coût mensuel estimé en euros
    """
    scale_factors = {
        "small": 0.3,
        "medium": 1.0,
        "large": 2.5,
    }

    base_cost = STACK_MONTHLY_COSTS.get(stack_name, 2000)  # valeur par défaut
    factor = scale_factors.get(scale, 1.0)
    return round(base_cost * factor, 2)


def suggest_target_stacks(
    current_stack: str,
    coupling_score: float,
    cohesion_score: float,
) -> list[str]:
    """
    Suggère 1 à 3 stacks cibles "typiques" pour le simulateur de migration,
    à partir de signaux RÉELS uniquement (stack actuelle, couplage, cohésion
    — tous calculés par architect_insight/metrics/patterns.py). Aucune donnée
    inventée (pas de "profil"/secteur, qui n'existe pas dans un vrai scan).

    Heuristique volontairement simple (seuils modifiables) :
    - Part de DEFAULT_MIGRATION_SUGGESTIONS[current_stack] comme base.
    - Si le couplage est élevé (>= 7.0/10), priorise une stack orientée
      découplage/typage statique (Go) en tête de liste.
    - Exclut toujours current_stack du résultat.
    - Si le résultat est vide (stack inconnue ou déjà "optimale"), replie sur
      les 2 stacks les moins chères de STACK_MONTHLY_COSTS.
    - Plafonné à 3 suggestions.
    """
    suggestions = [
        s for s in DEFAULT_MIGRATION_SUGGESTIONS.get(current_stack, []) if s != current_stack
    ]

    if coupling_score >= 7.0 and current_stack != "Go":
        # Move Go to the front (whether or not it was already in the list) —
        # a high-coupling signal should make it the top suggestion, not just
        # "present somewhere."
        if "Go" in suggestions:
            suggestions.remove("Go")
        suggestions.insert(0, "Go")

    if not suggestions:
        cheapest = sorted(STACK_MONTHLY_COSTS, key=lambda s: STACK_MONTHLY_COSTS[s])
        suggestions = [s for s in cheapest if s != current_stack][:2]

    # Dédoublonne en gardant l'ordre (Go peut avoir été insérée en double)
    seen: set[str] = set()
    deduped = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            deduped.append(s)

    return deduped[:3]


def compute_full_report(
    current_stack: str,
    target_stack: Optional[str],
    duration_days: int,
    team_size: int,
    current_cloud_cost: Optional[float] = None,
    scale: str = "medium",
    hourly_rate: float = 80.0,
) -> CostReport:
    """
    Génère le rapport financier complet.
    
    Args:
        current_stack: Nom de la stack actuelle
        target_stack: Stack recommandée (None si pas de migration)
        duration_days: Durée de migration (0 si pas de migration)
        team_size: Taille d'équipe recommandée
        current_cloud_cost: Coût cloud actuel (si connu, sinon estimé)
        scale: Niveau de charge ("small", "medium", "large")
        hourly_rate: Taux horaire moyen
    
    Returns:
        CostReport complet
    """
    # Estimer le coût cloud actuel si non fourni
    if current_cloud_cost is None:
        current_cloud_cost = estimate_cloud_cost_from_stack(current_stack, scale)
    
    # Si pas de migration, les coûts restent les mêmes
    if target_stack is None or target_stack == current_stack:
        return CostReport(
            migration_cost=0.0,
            current_cloud_cost=current_cloud_cost,
            target_cloud_cost=current_cloud_cost,
            monthly_savings=0.0,
            roi_months=float('inf'),
            payback_months=float('inf'),
            cost_confidence="high",
        )
    
    # Coût de migration (si applicable)
    if duration_days > 0 and team_size > 0:
        migration_cost = calculate_migration_cost(duration_days, team_size, hourly_rate)
    else:
        migration_cost = 0.0
    
    # Coût cloud cible
    target_cloud_cost = estimate_cloud_cost_from_stack(target_stack, scale)
    
    # Économies mensuelles
    monthly_savings, delta_pct = calculate_cloud_cost_delta(
        current_cloud_cost, target_cloud_cost
    )
    
    # ROI
    roi_months = calculate_roi(migration_cost, monthly_savings)
    
    # Niveau de confiance (basé sur la précision des estimations)
    if delta_pct > 20 and migration_cost > 0:
        confidence = "high"
    elif delta_pct > 10 and migration_cost > 0:
        confidence = "medium"
    else:
        confidence = "low"
    
    return CostReport(
        migration_cost=migration_cost,
        current_cloud_cost=current_cloud_cost,
        target_cloud_cost=target_cloud_cost,
        monthly_savings=monthly_savings,
        roi_months=roi_months,
        payback_months=roi_months,  # identique pour ce modèle simplifié
        cost_confidence=confidence,
    )


def cost_report_to_dict(report: CostReport) -> dict:
    """Convertit un CostReport en dictionnaire JSON-serializable."""
    return {
        "migration_cost": report.migration_cost,
        "current_cloud_cost": report.current_cloud_cost,
        "target_cloud_cost": report.target_cloud_cost,
        "monthly_savings": report.monthly_savings,
        "roi_months": report.roi_months,
        "payback_months": report.payback_months,
        "cost_confidence": report.cost_confidence,
    }