"""Regression test: training_data.jsonl must stay consistent with the
CURRENT validate_output() anti-bias rules (health-band/migration coherence,
no foreign-stack mentions in project_description).

Guards against the _MIGRATION_KEYWORDS regex bug found while adding the
foreign-stack heuristic: the old "migrat" stem silently never matched the
French verb "migrer", so ~10% of training_data.jsonl (40/384) had violated
the "healthy -> no migration recommended" / "critical -> real action
proposed" guarantee without ever being flagged. Those were moved to
to_review.jsonl by dataset_generation/reconcile_flagged_examples.py — this
test ensures no similarly-inconsistent example creeps back in.
"""

import json
from pathlib import Path

from dataset_generation.generate_dataset import _foreign_stack_mentions, _recommends_migration
from dataset_generation.scenario_axes import sample_scenarios

DATA_DIR = Path(__file__).resolve().parent.parent / "dataset_generation"


def _load_records():
    path = DATA_DIR / "training_data.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_no_healthy_or_critical_inconsistency_in_training_data():
    records = _load_records()
    max_index = max(int(r["scenario_id"].removeprefix("scn_")) for r in records)
    scenarios_by_id = {s.scenario_id: s for s in sample_scenarios(max_index + 1, seed=42)}

    violations = []
    for record in records:
        output = record.get("output", {})
        band = record.get("health_band")
        if band == "healthy" and _recommends_migration(output.get("recommendation", "")):
            violations.append((record["scenario_id"], "healthy+migration"))
        if band == "critical" and not _recommends_migration(
            output.get("recommendation", "") + " " + output.get("analysis", "")
        ):
            violations.append((record["scenario_id"], "critical+no-action"))

        scenario = scenarios_by_id.get(record.get("scenario_id"))
        if scenario and _foreign_stack_mentions(output.get("project_description", ""), scenario):
            violations.append((record["scenario_id"], "foreign-stack"))

    assert not violations, f"{len(violations)} inconsistent training examples: {violations[:10]}..."
