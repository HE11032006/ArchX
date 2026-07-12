"""
reconcile_flagged_examples.py
-------------------------------
One-shot maintenance script: re-validates every record already written to
training_data.jsonl against the CURRENT validate_output() consistency checks
(health-band/migration coherence, foreign-stack mentions), and moves any
record that would now be flagged into to_review.jsonl.

Why this exists: _MIGRATION_KEYWORDS used to require the English/nominal
stem "migrat" and silently failed to match the French verb "migrer", so the
healthy-band/critical-band anti-bias guard rails in validate_output() never
actually fired for a large share of French examples. That bug is now fixed
(see generate_dataset.py), but ~10% of the examples already written to
training_data.jsonl were validated under the broken regex and need to be
re-triaged rather than silently trained on.

No Teacher API calls: reuses the deterministic sample_scenarios(seed=42) to
reconstruct each record's Scenario, exactly like backfill_stack_fields.py.

Usage:
    python -m dataset_generation.reconcile_flagged_examples
"""

from __future__ import annotations

import json
from pathlib import Path

from .generate_dataset import _foreign_stack_mentions, _recommends_migration
from .scenario_axes import Scenario, sample_scenarios

_BASE_DIR = Path(__file__).resolve().parent
_TRAINING_PATH = _BASE_DIR / "training_data.jsonl"
_REVIEW_PATH = _BASE_DIR / "to_review.jsonl"


def _flag_reason(record: dict, scenario: Scenario) -> str | None:
    output = record.get("output", {})
    band = record.get("health_band")

    if band == "healthy" and _recommends_migration(output.get("recommendation", "")):
        return "healthy mais recommande une migration (re-triage post-fix _MIGRATION_KEYWORDS)"

    if band == "critical" and not _recommends_migration(
        output.get("recommendation", "") + " " + output.get("analysis", "")
    ):
        return "critical sans action structurante claire (re-triage post-fix _MIGRATION_KEYWORDS)"

    foreign = _foreign_stack_mentions(output.get("project_description", ""), scenario)
    if foreign:
        return f"project_description mentionne une stack étrangère : {sorted(foreign)}"

    return None


def main() -> None:
    if not _TRAINING_PATH.exists():
        print("training_data.jsonl introuvable, rien à faire.")
        return

    records = [json.loads(line) for line in _TRAINING_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    max_index = max(int(r["scenario_id"].removeprefix("scn_")) for r in records if "scenario_id" in r)
    scenarios_by_id = {s.scenario_id: s for s in sample_scenarios(max_index + 1, seed=42)}
    print(f"[INFO] {len(scenarios_by_id)} scénarios régénérés localement (seed=42, aucun appel API).")

    kept, moved = [], []
    for record in records:
        scenario = scenarios_by_id.get(record.get("scenario_id"))
        if scenario is None:
            kept.append(record)
            continue
        reason = _flag_reason(record, scenario)
        if reason:
            record["reconciliation_reason"] = reason
            moved.append(record)
        else:
            kept.append(record)

    if not moved:
        print("Aucun exemple à re-trier — training_data.jsonl est déjà cohérent.")
        return

    _TRAINING_PATH.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in kept) + "\n", encoding="utf-8"
    )
    with open(_REVIEW_PATH, "a", encoding="utf-8") as review_f:
        for record in moved:
            review_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[training_data.jsonl] {len(kept)} exemples conservés, {len(moved)} déplacés vers to_review.jsonl.")


if __name__ == "__main__":
    main()
