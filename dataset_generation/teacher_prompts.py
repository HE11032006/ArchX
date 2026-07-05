"""
teacher_prompts.py
--------------------
Construit les prompts envoyés au modèle enseignant (Claude/GPT) pour chaque
scénario, dans la langue demandée. Deux garde-fous sont codés en dur dans le
system prompt, pas laissés à la discrétion du teacher :

  1. Jamais de montant en $/€ ni de ROI en mois — ces valeurs sont calculées
     par une fonction séparée (voir cost_calculator.py, à écrire ensuite),
     jamais générées par un LLM.
  2. La recommandation doit être strictement justifiée par les métriques
     données. Si le projet est globalement sain, le teacher DOIT recommander
     de ne pas migrer — sinon on retombe sur un dataset biaisé "toujours
     réécrire".
"""

from __future__ import annotations

from .scenario_axes import Scenario

_SYSTEM_FR = """Tu es un architecte logiciel senior avec plus de 15 ans d'expérience, \
qui a vu des dizaines de migrations technologiques réussir et échouer. Ton style : direct, \
factuel, jamais dogmatique sur une techno. Tu sais qu'un rewrite complet est souvent la \
mauvaise décision — tu ne le recommandes que quand les faits le justifient clairement.

RÈGLES STRICTES :
- N'invente JAMAIS de montant en euros/dollars, ni de durée de ROI en mois. Ces valeurs \
seront calculées séparément par un outil. N'inclus aucun champ "cost" ou "roi" dans ta réponse.
- Ta recommandation doit découler logiquement des métriques fournies. Si les métriques sont \
globalement saines (faible couplage, bonne couverture de tests, peu d'anti-patterns), tu DOIS \
recommander de NE PAS migrer, et proposer plutôt des améliorations incrémentales ciblées.
- Pour les durées de phases, donne une fourchette réaliste en jours (ex: "10-15 jours"), \
jamais un chiffre unique à la journée près.
- Réponds uniquement en JSON valide, dans la structure demandée, en français naturel et \
professionnel (pas de traduction mot à mot depuis l'anglais)."""

_SYSTEM_EN = """You are a senior software architect with 15+ years of experience, who has \
seen dozens of technology migrations succeed and fail. Your style: direct, factual, never \
dogmatic about any particular technology. You know a full rewrite is often the wrong call — \
you only recommend one when the facts clearly justify it.

STRICT RULES:
- NEVER invent a dollar/euro amount or a ROI duration in months. These values will be \
computed separately by a tool. Do not include any "cost" or "roi" field in your answer.
- Your recommendation must follow logically from the given metrics. If the metrics are \
overall healthy (low coupling, good test coverage, few anti-patterns), you MUST recommend \
NOT migrating, and instead propose targeted incremental improvements.
- For phase durations, give a realistic day range (e.g. "10-15 days"), never a single \
day-precise number.
- Respond only in valid JSON, in the requested structure, in natural, professional English \
(not a literal translation)."""

_OUTPUT_SCHEMA_HINT = """{
  "project_description": "...",
  "analysis": "...",
  "recommendation": "...",
  "phases": [{"phase": 1, "action": "...", "duration_days_range": "..."}],
  "risk_assessment": "..."
}"""


def _user_prompt_fr(s: Scenario) -> str:
    ap = "\n".join(f"  - {a['type']} ({a['severity']}) dans {a['location']}" for a in s.anti_patterns) or "  - Aucun anti-pattern significatif détecté"
    m = s.metrics
    return f"""Voici les données RÉELLES (déjà calculées par des outils d'analyse statique et git) d'un projet à analyser :

CONTEXTE
- Secteur : {s.sector}
- Équipe : {s.team_size} développeurs ({s.pct_junior}% juniors, {s.pct_senior}% seniors)
- Codebase : {s.codebase_age_years} ans, stack {s.language}/{s.framework}/{s.database}
- Contrainte dominante identifiée par l'équipe : {s.dominant_constraint}

MÉTRIQUES CALCULÉES
- Score de couplage : {m['coupling_score']}/10
- Score de cohésion : {m['cohesion_score']}/10
- Couverture de tests estimée : {m['test_coverage_estimate']}%
- Complexité cyclomatique moyenne : {m['avg_cyclomatic_complexity']}
- Ratio de commits correctifs sur le fichier le plus chaud : {m['top_hotspot_bugfix_ratio']}

ANTI-PATTERNS DÉTECTÉS
{ap}

Rédige d'abord une description de projet réaliste (2-3 phrases, "project_description") qui \
intègre ce contexte naturellement, PUIS ton analyse d'architecte senior en JSON selon ce schéma :
{_OUTPUT_SCHEMA_HINT}

Rappel : pas de montant en euros, pas de ROI en mois, pas de recommandation de migration si \
les métriques ne la justifient pas clairement."""


def _user_prompt_en(s: Scenario) -> str:
    ap = "\n".join(f"  - {a['type']} ({a['severity']}) in {a['location']}" for a in s.anti_patterns) or "  - No significant anti-pattern detected"
    m = s.metrics
    return f"""Here is the REAL data (already computed by static analysis and git tools) for a project to analyze:

CONTEXT
- Sector: {s.sector}
- Team: {s.team_size} developers ({s.pct_junior}% junior, {s.pct_senior}% senior)
- Codebase: {s.codebase_age_years} years old, stack {s.language}/{s.framework}/{s.database}
- Dominant constraint identified by the team: {s.dominant_constraint}

COMPUTED METRICS
- Coupling score: {m['coupling_score']}/10
- Cohesion score: {m['cohesion_score']}/10
- Estimated test coverage: {m['test_coverage_estimate']}%
- Average cyclomatic complexity: {m['avg_cyclomatic_complexity']}
- Bugfix-commit ratio on the hottest file: {m['top_hotspot_bugfix_ratio']}

DETECTED ANTI-PATTERNS
{ap}

First write a realistic project description (2-3 sentences, "project_description") that \
naturally incorporates this context, THEN your senior architect analysis as JSON following \
this schema:
{_OUTPUT_SCHEMA_HINT}

Reminder: no dollar amount, no ROI in months, no migration recommendation if the metrics \
don't clearly justify one."""


def build_prompts(scenario: Scenario, language: str) -> tuple[str, str]:
    """Retourne (system_prompt, user_prompt) pour la langue demandée ('fr' ou 'en')."""
    if language == "fr":
        return _SYSTEM_FR, _user_prompt_fr(scenario)
    elif language == "en":
        return _SYSTEM_EN, _user_prompt_en(scenario)
    raise ValueError(f"Langue non supportée : {language} (utilise 'fr' ou 'en')")
