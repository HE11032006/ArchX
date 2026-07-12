"""Unit tests for the deterministic migration-simulator helpers.

Route-level behavior is covered in test_api_routes.py; these test the pure
functions directly (table lookup, coupling override, current-stack exclusion,
empty-table fallback).
"""

from api.services.pipeline import derive_current_stack, derive_duration_days
from architect_insight.metrics.cost_calculator import STACK_MONTHLY_COSTS, suggest_target_stacks


def test_derive_current_stack_strips_parenthetical():
    assert derive_current_stack({"architecture_pattern": "Django (MVT)"}) == "Django"


def test_derive_current_stack_defaults_to_django():
    assert derive_current_stack({}) == "Django"


def test_derive_duration_days_sums_and_rounds_phases():
    phases = [{"duration_days_range": "10-15"}, {"duration_days_range": "5-10"}]
    assert derive_duration_days(phases) == 20  # (12.5 + 7.5) = 20


def test_derive_duration_days_empty_phases():
    assert derive_duration_days([]) == 0


def test_suggest_target_stacks_uses_table_and_excludes_current():
    suggestions = suggest_target_stacks("Rails", coupling_score=3.0, cohesion_score=7.0)
    assert "Rails" not in suggestions
    assert suggestions  # Rails has real table entries


def test_suggest_target_stacks_high_coupling_prioritizes_go():
    suggestions = suggest_target_stacks("Django", coupling_score=8.0, cohesion_score=3.0)
    assert suggestions[0] == "Go"


def test_suggest_target_stacks_falls_back_to_cheapest_when_table_empty():
    # Rust has an empty suggestion list in DEFAULT_MIGRATION_SUGGESTIONS and is
    # already the cheapest stack itself, so the fallback should still exclude it.
    suggestions = suggest_target_stacks("Rust", coupling_score=1.0, cohesion_score=8.0)
    assert "Rust" not in suggestions
    assert suggestions


def test_suggest_target_stacks_capped_at_three():
    suggestions = suggest_target_stacks("Django", coupling_score=8.0, cohesion_score=1.0)
    assert len(suggestions) <= 3


def test_stack_monthly_costs_has_all_ten_known_stacks():
    assert len(STACK_MONTHLY_COSTS) == 10
    assert STACK_MONTHLY_COSTS["Go"] == 1200
