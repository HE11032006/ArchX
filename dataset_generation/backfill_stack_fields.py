"""
backfill_stack_fields.py
-------------------------
One-shot maintenance script: adds "language" and "database" to the "input"
block of every existing record in training_data.jsonl / to_review.jsonl,
without any Teacher API calls.

Why: those records were generated before generate_dataset.py started saving
scenario.language/scenario.database into record["input"] (see git history).
sample_scenarios(n, seed=42) is deterministic, so we can regenerate the exact
same Scenario objects locally and backfill by scenario_id.

Usage:
    python -m dataset_generation.backfill_stack_fields
    python -m dataset_generation.backfill_stack_fields --files training_data.jsonl to_review.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .scenario_axes import sample_scenarios

_SCENARIO_ID_RE = re.compile(r'"scenario_id":\s*"scn_(\d+)"')


def _max_scenario_index(paths: list[Path]) -> int:
    max_index = -1
    for path in paths:
        if not path.exists():
            continue
        for match in _SCENARIO_ID_RE.finditer(path.read_text(encoding="utf-8")):
            max_index = max(max_index, int(match.group(1)))
    return max_index


def backfill_file(path: Path, scenarios_by_id: dict) -> tuple[int, int]:
    """Returns (updated_count, already_had_fields_count)."""
    if not path.exists():
        return 0, 0

    lines = path.read_text(encoding="utf-8").splitlines()
    updated, already_ok = 0, 0
    out_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        scenario_id = record.get("scenario_id")
        scenario = scenarios_by_id.get(scenario_id)

        input_block = record.get("input", {})
        input_block.pop("database", None)  # stale key name from an earlier version of this script
        if "language" in input_block and "database_name" in input_block:
            already_ok += 1
        elif scenario is not None:
            input_block["language"] = scenario.language
            input_block["database_name"] = scenario.database
            record["input"] = input_block
            updated += 1
        # else: scenario_id not found among regenerated scenarios — leave untouched,
        # will show up in the summary so it can be investigated.

        out_lines.append(json.dumps(record, ensure_ascii=False))

    path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return updated, already_ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--files",
        nargs="+",
        default=["training_data.jsonl", "to_review.jsonl"],
        help="Fichiers JSONL à backfiller (relatifs à dataset_generation/)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    paths = [base_dir / f for f in args.files]

    max_index = _max_scenario_index(paths)
    if max_index < 0:
        print("Aucun scenario_id trouvé, rien à faire.")
        return

    scenarios = sample_scenarios(max_index + 1, seed=42)
    scenarios_by_id = {s.scenario_id: s for s in scenarios}
    print(f"[INFO] {len(scenarios_by_id)} scénarios régénérés localement (seed=42, aucun appel API).")

    for path in paths:
        updated, already_ok = backfill_file(path, scenarios_by_id)
        print(f"[{path.name}] {updated} enregistrements complétés, {already_ok} déjà à jour.")


if __name__ == "__main__":
    main()
