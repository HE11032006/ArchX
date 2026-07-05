"""
generate_dataset.py
----------------------
Boucle sur les scénarios × langues, appelle le modèle enseignant, valide
chaque réponse (JSON bien formé + garde-fous respectés + cohérence logique
avec la bande de santé), et écrit un JSONL prêt pour le fine-tuning.

Nécessite une clé API (variable d'environnement OPENROUTER_API_KEY) et le
paquet `openai` installé.

Usage réel :
    export OPENROUTER_API_KEY=sk-or-v1-...
    python -m dataset_generation.generate_dataset --n 400 --out dataset.jsonl

Test sans réseau (dans ce sandbox) :
    python -m dataset_generation.generate_dataset --n 20 --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

from .scenario_axes import Scenario, sample_scenarios
from .teacher_prompts import build_prompts

REQUIRED_FIELDS = {"project_description", "analysis", "recommendation", "phases", "risk_assessment"}
FORBIDDEN_PATTERNS = [
    re.compile(r"\$\s?\d", re.IGNORECASE),
    re.compile(r"€\s?\d|\d\s?€", re.IGNORECASE),
    re.compile(r"\broi\b.{0,20}\bmonth", re.IGNORECASE),
    re.compile(r"\bretour sur investissement\b.{0,20}\bmois\b", re.IGNORECASE),
    re.compile(r'"cost"\s*:', re.IGNORECASE),
    re.compile(r'"roi"\s*:', re.IGNORECASE),
]

_MIGRATION_KEYWORDS = re.compile(
    r"migr|rewrite|réécri|réécr|remplacer la stack|switch to|passer à",
    re.IGNORECASE,
)
_NO_MIGRATION_PATTERNS = re.compile(
    r"ne pas migr|pas de migration|aucune migration|éviter (?:la|toute) migration|"
    r"do(?:n't| not) migrate|no migration|not migrating|without migrat|refrain from migrat",
    re.IGNORECASE,
)


def _recommends_migration(text: str) -> bool:
    """Détecte une recommandation de migration en tenant compte des négations
    ("ne pas migrer" ne doit pas être compté comme une recommandation de migrer)."""
    if _NO_MIGRATION_PATTERNS.search(text):
        return False
    return bool(_MIGRATION_KEYWORDS.search(text))


@dataclass
class ValidationResult:
    ok: bool
    reason: str | None = None
    needs_review: bool = False


def validate_output(raw_text: str, scenario: Scenario) -> tuple[dict | None, ValidationResult]:
    """Parse + applique les garde-fous. Retourne (data_ou_None, résultat)."""
    # 1. Le teacher répond parfois avec des ```json ... ``` autour du JSON
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(json)?", "", cleaned).rstrip("`").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return None, ValidationResult(ok=False, reason=f"JSON invalide : {exc}")

    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        return None, ValidationResult(ok=False, reason=f"Champs manquants : {missing}")

    # 2. Garde-fous : pas de $/€/ROI en mois inventés
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(cleaned):
            return None, ValidationResult(ok=False, reason=f"Motif interdit détecté : {pattern.pattern}")

    # 3. Cohérence logique : bande "healthy" mais recommandation qui parle de migration
    #    -> pas un rejet automatique (ça peut être légitime dans de rares cas), mais on
    #    flague pour relecture manuelle plutôt que de l'ajouter aveuglément au dataset.
    needs_review = False
    if scenario.health_band == "healthy" and _recommends_migration(data.get("recommendation", "")):
        needs_review = True

    if scenario.health_band == "critical" and not _recommends_migration(
        data.get("recommendation", "") + " " + data.get("analysis", "")
    ):
        needs_review = True  # cas critique mais aucune action structurante proposée : à vérifier aussi

    return data, ValidationResult(ok=True, needs_review=needs_review)


def call_teacher_model(system: str, user: str, model: str = "google/gemma-2-9b-it:free") -> str:
    """Appelle l'API OpenRouter. Nécessite `pip install openai` et OPENROUTER_API_KEY."""
    from openai import OpenAI
    import os

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", "dummy-key-for-dry-run")
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    )
    return response.choices[0].message.content


def generate_dataset(
    n_scenarios: int,
    languages: list[str],
    output_path: str,
    review_path: str,
    dry_run: bool = False,
    model: str = "google/gemma-2-9b-it:free",
) -> None:
    scenarios = sample_scenarios(n_scenarios)
    written, flagged, failed = 0, 0, 0

    with open(output_path, "w", encoding="utf-8") as out_f, open(review_path, "w", encoding="utf-8") as review_f:
        for scenario in scenarios:
            for lang in languages:
                system, user = build_prompts(scenario, lang)

                if dry_run:
                    # Ne consomme aucun appel réseau/API : sert à vérifier que les
                    # prompts se construisent bien et que le pipeline tourne.
                    print(f"[DRY-RUN] {scenario.scenario_id} ({lang}) — prompt {len(user)} caractères")
                    continue

                try:
                    raw = call_teacher_model(system, user, model=model)
                except Exception as exc:  # pragma: no cover
                    print(f"[ERREUR API] {scenario.scenario_id} ({lang}) : {exc}", file=sys.stderr)
                    failed += 1
                    continue

                data, result = validate_output(raw, scenario)
                record = {
                    "scenario_id": scenario.scenario_id,
                    "language": lang,
                    "health_band": scenario.health_band,
                    "input": {
                        "sector": scenario.sector,
                        "team_size": scenario.team_size,
                        "metrics": scenario.metrics,
                        "anti_patterns": scenario.anti_patterns,
                    },
                }

                if not result.ok:
                    record["error"] = result.reason
                    record["raw_output"] = raw
                    review_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    failed += 1
                    continue

                record["output"] = data
                if result.needs_review:
                    review_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    flagged += 1
                else:
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    written += 1

    if not dry_run:
        print(f"Terminé : {written} exemples valides -> {output_path}")
        print(f"          {flagged} exemples à relire (incohérence métriques/reco) -> {review_path}")
        print(f"          {failed} échecs (JSON invalide / garde-fou déclenché / erreur API) -> {review_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère le dataset de fine-tuning Architect-Insight")
    parser.add_argument("--n", type=int, default=400, help="Nombre de scénarios uniques (x nb de langues = total d'exemples)")
    parser.add_argument("--languages", nargs="+", default=["fr", "en"], choices=["fr", "en"])
    parser.add_argument("--out", default="training_data.jsonl")
    parser.add_argument("--review-out", default="to_review.jsonl")
    parser.add_argument("--model", default="google/gemma-2-9b-it:free", help="Modèle OpenRouter à utiliser (ex: google/gemini-2.5-pro, anthropic/claude-3.5-sonnet)")
    parser.add_argument("--dry-run", action="store_true", help="Ne fait aucun appel API, teste juste le pipeline")
    args = parser.parse_args()

    generate_dataset(
        n_scenarios=args.n,
        languages=args.languages,
        output_path=args.out,
        review_path=args.review_out,
        dry_run=args.dry_run,
        model=args.model,
    )


if __name__ == "__main__":
    main()
