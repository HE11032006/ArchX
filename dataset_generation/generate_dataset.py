"""
generate_dataset.py
----------------------
Boucle sur les scénarios × langues, appelle le modèle enseignant, valide
chaque réponse (JSON bien formé + garde-fous respectés + cohérence logique
avec la bande de santé), et écrit un JSONL prêt pour le fine-tuning.


Nécessite au moins une clé API parmi ANTHROPIC_API_KEY, GEMINI_API_KEY,
MISTRAL_API_KEY ou OPENROUTER_API_KEY (fallback ordonné, voir
call_teacher_model) et les paquets `anthropic`/`openai` installés.


Usage réel :
    export OPENROUTER_API_KEY=sk-or-v1-...
    python -m dataset_generation.generate_dataset --n 400 --out dataset.jsonl


Test sans réseau (dans ce sandbox) :
    python -m dataset_generation.generate_dataset --n 20 --dry-run
"""


from __future__ import annotations


import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError, APITimeoutError

from .scenario_axes import STACKS, Scenario, sample_scenarios
from .teacher_prompts import build_prompts


# Charger les variables d'environnement une seule fois au démarrage
load_dotenv()


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
    # "migr\w*" attrape "migrer"/"migration"/"migrate"/"migrating"/"migré" — l'ancien radical
    # "migrat" ne matchait QUE les formes en -ation/-ate, pas le verbe français "migrer".
    r"\b(migr\w*|rewrite|réécri|réécr|remplacer.*stack|switch.*to|passer.*à|adopt.*new.*stack)\b",
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


_ALL_STACK_TOKENS = {token for stack in STACKS for token in stack}

_AGE_PATTERN = re.compile(r"\b\d+([.,]\d+)?\s*(ans?|années?|years?|year-old)\b", re.IGNORECASE)
_TEAM_COMPOSITION_PATTERN = re.compile(r"\bjuniors?\b|\bseniors?\b", re.IGNORECASE)


def _foreign_stack_mentions(text: str, scenario: Scenario) -> set[str]:
    """Détecte des mentions de langage/framework/BDD qui n'appartiennent PAS à la
    stack de ce scénario dans `text` (censé décrire le projet TEL QU'IL EST, pas une
    cible de migration — c'est pourquoi on ne l'applique qu'à project_description,
    jamais à analysis/recommendation où citer une stack cible est légitime).

    Garde-fou complémentaire à generate_dataset.py's REQUIRED_FIELDS/FORBIDDEN_PATTERNS :
    empêche le teacher de décrire un projet avec une stack incohérente avec celle
    réellement fournie dans le scénario (root cause du bug de hallucination de stack
    constaté sur le modèle fine-tuné — voir training/format_for_training.py SYSTEM_PROMPT).
    """
    own_tokens = {scenario.language, scenario.framework, scenario.database}
    foreign_tokens = _ALL_STACK_TOKENS - own_tokens
    return {
        token for token in foreign_tokens
        if re.search(rf"\b{re.escape(token)}\b", text, re.IGNORECASE)
    }


def _undisclosed_stack_mentions(text: str) -> set[str]:
    """Pour un scénario stack_known=False : AUCUNE techno ne devrait apparaître,
    pas même la "vraie" stack du scénario (elle n'est par construction pas censée
    être connue). Contrairement à _foreign_stack_mentions, on n'exclut pas les
    tokens propres au scénario ici."""
    return {
        token for token in _ALL_STACK_TOKENS
        if re.search(rf"\b{re.escape(token)}\b", text, re.IGNORECASE)
    }


def _undisclosed_context_mentions(data: dict) -> list[str]:
    """Détecte des mentions de l'âge du projet ou de la composition junior/senior
    de l'équipe dans les champs narratifs de la réponse.

    Root cause d'un bug d'hallucination distinct de celui de la stack : ces deux
    infos sont données au teacher (teacher_prompts.py, section "CONTEXTE INTERNE")
    pour calibrer son raisonnement (risque perçu), mais ne sont JAMAIS fournies au
    student/production (api/services/pipeline.py ne peut pas les détecter). Avant
    ce fix, le teacher les narrait "naturellement" comme demandé par l'ancien
    prompt — confirmé sur ~92% (458/500) des exemples du dataset existant.
    """
    text = " ".join(str(data.get(k, "")) for k in ("project_description", "analysis", "risk_assessment"))
    hits = []
    if _AGE_PATTERN.search(text):
        hits.append("âge du projet")
    if _TEAM_COMPOSITION_PATTERN.search(text):
        hits.append("composition junior/senior")
    return hits


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
    #    flage pour relecture manuelle plutôt que de l'ajouter aveuglément au dataset.
    needs_review = False
    if scenario.health_band == "healthy" and _recommends_migration(data.get("recommendation", "")):
        needs_review = True


    if scenario.health_band == "critical" and not _recommends_migration(
        data.get("recommendation", "") + " " + data.get("analysis", "")
    ):
        needs_review = True  # cas critique mais aucune action structurante proposée : à vérifier aussi


    # 4. project_description mentionne une stack qui n'est pas celle du scénario
    #    -> le teacher a confondu/halluciné la stack, à relire avant d'entraîner dessus.
    description = data.get("project_description", "")
    if scenario.stack_known:
        if _foreign_stack_mentions(description, scenario):
            needs_review = True
    else:
        # stack_known=False : même la "vraie" stack du scénario ne devrait pas
        # apparaître, puisqu'elle est censée être non détectée à ce stade.
        if _undisclosed_stack_mentions(description):
            needs_review = True


    # 5. Âge du projet / composition junior-senior narrés alors qu'ils ne sont
    #    jamais fournis au student (voir _undisclosed_context_mentions).
    if _undisclosed_context_mentions(data):
        needs_review = True


    return data, ValidationResult(ok=True, needs_review=needs_review)


def call_teacher_model(system: str, user: str, model: str = "google/gemma-2-9b-it:free") -> str:
    """Appelle les fournisseurs IA disponibles avec fallback ordonné : Claude -> Gemini -> Mistral -> OpenRouter."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    mistral_key = os.environ.get("MISTRAL_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")

    # Étape 0 : Tenter Claude en premier — son suivi d'instructions est le plus fiable
    # pour respecter les règles nuancées du prompt (contexte interne vs. citable,
    # cf. teacher_prompts.py), ce qui compte particulièrement pour régénérer le
    # dataset proprement après le fix des bugs de hallucination.
    if anthropic_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            content = response.content[0].text
            if content:
                return content
        except Exception as e:
            print(f"  [CLAUDE FAILS] Erreur lors de l'appel Claude: {e}. Bascule sur Gemini...")

    # Étape 1 : Tenter Gemini (Google AI Studio)
    if gemini_key:
        try:
            client = OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=gemini_key
            )
            response = client.chat.completions.create(
                model="gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            )
            # Vérifier que le format de sortie est propre
            content = response.choices[0].message.content
            if content:
                return content
        except Exception as e:
            print(f"  [GEMINI FAILS] Erreur lors de l'appel Gemini: {e}. Bascule sur Mistral...")

    # Étape 2 : Tenter Mistral API
    if mistral_key:
        try:
            client = OpenAI(
                base_url="https://api.mistral.ai/v1",
                api_key=mistral_key
            )
            response = client.chat.completions.create(
                model="mistral-small-latest",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            )
            content = response.choices[0].message.content
            if content:
                return content
        except Exception as e:
            print(f"  [MISTRAL FAILS] Erreur lors de l'appel Mistral: {e}. Bascule sur OpenRouter...")

    # Étape 3 : Fallback final OpenRouter (si clés disponibles)
    if openrouter_key:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        fallback_models = [
            model,
            "google/gemma-4-31b-it:free",
            "google/gemma-4-26b-a4b-it:free",
            "openrouter/free"
        ]
        for attempt in range(5):
            current_model = fallback_models[min(attempt, len(fallback_models) - 1)]
            try:
                response = client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                wait = 10 * (attempt + 1)
                print(f"  [OPENROUTER RETRY] {current_model} échoué ({e}) — attente {wait}s...")
                time.sleep(wait)

    # Si rien n'a marché ou si aucune clé n'est définie
    raise RuntimeError(
        "Échec de tous les fournisseurs d'API (Gemini, Mistral et OpenRouter). "
        "Veuillez définir au moins une clé API valide (GEMINI_API_KEY, MISTRAL_API_KEY ou OPENROUTER_API_KEY) dans votre .env"
    )


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

    # S'assurer que les répertoires de sortie existent
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(review_path).parent.mkdir(parents=True, exist_ok=True)

    from tqdm import tqdm
    import itertools

    # --- SYSTÈME DE CHECKPOINT (REPRISE) ---
    # Lire les (scenario_id, language) déjà présents dans les fichiers de sortie
    # afin de pouvoir relancer le script sans recommencer depuis le début.
    def _load_done_keys(path: str) -> set:
        done = set()
        p = Path(path)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        done.add((rec["scenario_id"], rec["language"]))
                    except (json.JSONDecodeError, KeyError):
                        pass
        return done

    done_keys = _load_done_keys(output_path) | _load_done_keys(review_path)
    if done_keys:
        print(f"[REPRISE] {len(done_keys)} exemples déjà traités, on continue là où on s'est arrêté...")

    all_pairs = list(itertools.product(scenarios, languages))
    remaining = [(s, l) for s, l in all_pairs if (s.scenario_id, l) not in done_keys]
    print(f"[INFO] {len(all_pairs) - len(remaining)} ignorés (déjà faits) — {len(remaining)} restants à générer.")

    # Mode "append" pour ne pas écraser ce qui a déjà été généré
    with open(output_path, "a", encoding="utf-8") as out_f, open(review_path, "a", encoding="utf-8") as review_f:
        for scenario, lang in tqdm(remaining, desc="Appels API en cours", total=len(remaining)):
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
                base_input = {
                    "sector": scenario.sector,
                    "team_size": scenario.team_size,
                    "metrics": scenario.metrics,
                    "anti_patterns": scenario.anti_patterns,
                    # Uniquement les champs de scenario_axes.Scenario qu'un vrai
                    # collector.py peut honnêtement fournir en production
                    # (voir api/services/pipeline.py::build_prompt_from_metrics).
                    # pct_junior/pct_senior/codebase_age_years/dominant_constraint/
                    # framework sont vus par le teacher (teacher_prompts.py) mais
                    # PAS inclus ici exprès : les inclure entraînerait le modèle à
                    # s'attendre à des infos qu'on ne peut pas lui fournir réellement,
                    # et il les halluciné à la place (cf. bug constaté en test manuel).
                }
                if scenario.stack_known:
                    # ~75% des scénarios : le student voit language/database_name,
                    # exactement comme quand collector.py détecte réellement la stack.
                    base_input["language"] = scenario.language
                    base_input["database_name"] = scenario.database
                # Sinon (~25% des scénarios) : ces clés sont absentes, comme quand
                # collector.py échoue à fingerprinter le repo — le student doit
                # aussi voir ce cas à l'entraînement, sinon il ne sait que
                # halluciner une stack quand l'info manque réellement en prod.
                record = {
                    "scenario_id": scenario.scenario_id,
                    "language": lang,
                    "health_band": scenario.health_band,
                    "input": base_input,
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
        print(f"         {flagged} exemples à relire (incohérence métriques/reco) -> {review_path}")
        print(f"         {failed} échecs (JSON invalide / garde-fou déclenché / erreur API) -> {review_path}")


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