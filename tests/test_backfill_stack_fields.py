"""Regression test for the training_data.jsonl / to_review.jsonl backfill.

Locks in: (1) every record's input carries language/database_name IF AND ONLY
IF its scenario has stack_known=True (~75% of scenarios — the other ~25%
intentionally omit them, so the student also learns the "stack not detected
-> don't invent one" case, see scenario_axes.py::Scenario.stack_known and the
dataset regeneration that fixed the stack/age/team hallucination bugs), and
(2) re-running the backfill script is a no-op (idempotent) — it must not
silently drift the dataset on a second run.
"""

import json
from pathlib import Path

from dataset_generation.backfill_stack_fields import backfill_file
from dataset_generation.scenario_axes import sample_scenarios

DATA_DIR = Path(__file__).resolve().parent.parent / "dataset_generation"


def _load_all(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_training_records_have_stack_fields_iff_stack_known():
    records = _load_all(DATA_DIR / "training_data.jsonl")
    assert records, "training_data.jsonl should not be empty"

    max_index = max(int(r["scenario_id"].removeprefix("scn_")) for r in records)
    scenarios_by_id = {s.scenario_id: s for s in sample_scenarios(max_index + 1, seed=42)}

    for record in records:
        assert "database" not in record["input"]  # stale key name, must not linger

        scenario = scenarios_by_id.get(record["scenario_id"])
        if scenario is None or scenario.stack_known:
            assert "language" in record["input"]
            assert "database_name" in record["input"]
        else:
            assert "language" not in record["input"]
            assert "database_name" not in record["input"]


def test_backfill_is_idempotent(tmp_path):
    scenarios = sample_scenarios(250, seed=42)
    scenarios_by_id = {s.scenario_id: s for s in scenarios}

    sample_path = tmp_path / "sample.jsonl"
    sample_path.write_text(
        "\n".join(
            json.dumps({"scenario_id": "scn_0000", "input": {"sector": "e-commerce"}})
            for _ in range(1)
        )
        + "\n",
        encoding="utf-8",
    )

    updated_1, already_ok_1 = backfill_file(sample_path, scenarios_by_id)
    updated_2, already_ok_2 = backfill_file(sample_path, scenarios_by_id)

    assert updated_1 == 1 and already_ok_1 == 0
    assert updated_2 == 0 and already_ok_2 == 1
