"""End-to-end smoke tests for run_pipeline.

Locks in: (1) the response always carries a top-level "inference_mode" key
so the frontend can show whether a real fine-tuned response or the mock
fallback was used (and it's popped out of "recommendation", not leaked into
the model's own JSON schema), and (2) the duration_days_range fix
(see test_pipeline.py) actually flows through run_pipeline into a nonzero
migration_cost when the model recommends a migration.
"""

from pathlib import Path

import api.services.pipeline as pipeline

DEMO_PROJECTS_DIR = Path(__file__).resolve().parent.parent / "demo_projects"


def test_run_pipeline_mock_mode_reports_inference_mode():
    report = pipeline.run_pipeline(str(DEMO_PROJECTS_DIR / "django_app"), mock=True)

    assert report["inference_mode"] == "mock"
    assert "inference_mode" not in report["recommendation"]  # popped, not leaked into the model schema


def test_run_pipeline_migration_cost_uses_duration_days_range(monkeypatch):
    # Simulate a real fine-tuned response recommending a migration, with phases
    # shaped like the model actually outputs (duration_days_range, not duration_days).
    fake_recommendation = {
        "project_description": "...",
        "analysis": "Go migration recommended.",
        "recommendation": "migration",
        "phases": [
            {"phase": 1, "action": "Rewrite core in Go", "duration_days_range": "15-20"},
            {"phase": 2, "action": "Migrate data layer", "duration_days_range": "5-10"},
        ],
        "risk_assessment": "Medium",
        "inference_mode": "fine-tuned",
    }
    monkeypatch.setattr(pipeline, "call_model", lambda *a, **kw: dict(fake_recommendation))

    report = pipeline.run_pipeline(str(DEMO_PROJECTS_DIR / "django_app"), mock=False, model_path="fake")

    # (17.5 + 7.5) rounded = 25 days effective duration -> must produce a real, nonzero cost.
    assert report["inference_mode"] == "fine-tuned"
    assert report["cost_analysis"]["migration_cost"] > 0
