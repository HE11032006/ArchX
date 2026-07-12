"""
fix_prompts.py
----------------
Génère jusqu'à 6 prompts prêts à coller dans un assistant IA local (Copilot,
Cursor, un LLM local...) pour corriger les anti-patterns détectés. Purement
déterministe (templates + string formatting) — aucun appel LLM, donc aucun
coût d'inférence supplémentaire.
"""

from __future__ import annotations

# Un template par type réel d'anti-pattern (voir architect_insight/metrics/
# patterns.py::detect_anti_patterns — ce sont les 4 SEULS types qu'il produit
# aujourd'hui). "Fichier non analysable" est un marqueur d'erreur de parsing,
# pas un anti-pattern — il n'a donc volontairement pas de template ici.
PROMPT_TEMPLATES: dict[str, str] = {
    "God Class": (
        "Refactor the God Class at {location}. {detail}. Propose a concrete "
        "extraction plan: identify 2-4 cohesive responsibility clusters among "
        "its methods, extract each into its own class (Single Responsibility "
        "Principle), and show the resulting class layout before/after. Keep "
        "the public API backward-compatible where feasible."
    ),
    "Long Method": (
        "Refactor the long method at {location}. {detail}. Break it into "
        "smaller, named helper functions (Extract Method), each with one "
        "clear purpose. Preserve behavior — run it against existing tests, "
        "or specify the unit tests to add first if none exist for this "
        "function."
    ),
    "Long Parameter List": (
        "Refactor the function at {location}. {detail}. Group the related "
        "parameters into a single parameter object/dataclass (Introduce "
        "Parameter Object), or split the function into smaller functions "
        "each needing fewer inputs. Update all call sites."
    ),
    "High Coupling (fichier)": (
        "Reduce coupling in {location}. {detail}. Identify which imports are "
        "structural (core domain) vs incidental (utility/infra), then either "
        "(1) introduce an interface/abstraction boundary to invert some "
        "dependencies, or (2) split this file's responsibilities across "
        "modules aligned to a single concern each."
    ),
}

_EXCLUDED_TYPES = {"Fichier non analysable"}

FALLBACK_TEMPLATE = (
    "No Python-AST anti-pattern findings are available for this repository "
    "(anti-pattern detection currently covers Python only). Based on the "
    "real structural signals collected — coupling {coupling_score}/10, "
    "cohesion {cohesion_score}/10, average cyclomatic complexity "
    "{avg_cyclomatic_complexity}, architecture pattern '{architecture_pattern}' "
    "— review the highest-complexity file '{top_hotspot_file}' (complexity "
    "{top_hotspot_complexity}) for extraction opportunities, and consider "
    "reducing cross-module coupling if the score above is high."
)


def generate_fix_prompts(
    anti_patterns: list[dict],
    metrics: dict | None = None,
    max_prompts: int = 6,
) -> list[dict]:
    """Deterministic, template-based fix prompts — pure string formatting,
    no LLM call. Returns [{"type", "location", "prompt", "fallback"}, ...].
    """
    real_findings = [p for p in anti_patterns if p.get("type") not in _EXCLUDED_TYPES]

    prompts = []
    for finding in real_findings[:max_prompts]:
        template = PROMPT_TEMPLATES.get(finding.get("type", ""))
        if not template:
            continue
        prompts.append({
            "type": finding["type"],
            "location": finding.get("location", ""),
            "prompt": template.format(
                location=finding.get("location", "unknown location"),
                detail=finding.get("detail", ""),
            ),
            "fallback": False,
        })

    if prompts or not metrics:
        return prompts

    hotspots = metrics.get("complexity_hotspots") or []
    if not hotspots:
        return []

    top_hotspot = max(hotspots, key=lambda h: h.get("max_complexity", 0))
    fallback_prompt = FALLBACK_TEMPLATE.format(
        coupling_score=metrics.get("coupling_score", "N/A"),
        cohesion_score=metrics.get("cohesion_score", "N/A"),
        avg_cyclomatic_complexity=metrics.get("avg_cyclomatic_complexity", "N/A"),
        architecture_pattern=metrics.get("architecture_pattern", "unknown"),
        top_hotspot_file=top_hotspot.get("file", "unknown"),
        top_hotspot_complexity=top_hotspot.get("max_complexity", "N/A"),
    )
    return [{
        "type": "generic",
        "location": top_hotspot.get("file", ""),
        "prompt": fallback_prompt,
        "fallback": True,
    }]
