"""Regression tests for api.services.pipeline duration-parsing logic.

Locks in the fix for the duration_days_range bug: the fine-tuned model (and
100% of dataset_generation/training_data.jsonl) emits "duration_days_range"
(e.g. "15-20") in each phase, not the "duration_days" int that
run_pipeline used to read — which meant migration_cost was always ~0.
"""

from api.services.pipeline import _phase_duration_days


def test_duration_days_range_is_averaged():
    # Real shape seen from the fine-tuned model's output.
    assert _phase_duration_days({"duration_days_range": "15-20"}) == 17.5


def test_duration_days_range_with_spaces_and_dash_variants():
    assert _phase_duration_days({"duration_days_range": "10 - 15"}) == 12.5
    assert _phase_duration_days({"duration_days_range": "10–15"}) == 12.5  # en dash


def test_duration_days_range_single_number():
    assert _phase_duration_days({"duration_days_range": "10"}) == 10


def test_explicit_duration_days_takes_priority():
    # Back-compat: if a producer ever emits the plain int key, trust it.
    assert _phase_duration_days({"duration_days": 12, "duration_days_range": "1-2"}) == 12


def test_missing_duration_fields_returns_zero():
    assert _phase_duration_days({"action": "Refactor God Classes"}) == 0


def test_unparseable_range_returns_zero():
    assert _phase_duration_days({"duration_days_range": "unspecified"}) == 0
