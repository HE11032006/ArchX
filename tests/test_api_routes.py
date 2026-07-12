"""Route-level tests for the feedback and migration-simulator endpoints.

Builds completed Job entries directly in job_store (bypassing the real
analyze/background-task flow, which needs a real repo) — same style as
unit-testing the route handlers in isolation.
"""

import json

from fastapi.testclient import TestClient

from api.main import app
from api.services.job_store import job_store

client = TestClient(app)

_FAKE_METRICS = {
    "architecture_pattern": "Django (MVT)",
    "coupling_score": 8.0,
    "cohesion_score": 2.0,
}


def _make_completed_job(**overrides):
    job = job_store.create(repo_path="fake/repo", language="fr", team_size=8, hourly_rate=80.0)
    report = {
        "metrics": _FAKE_METRICS,
        "recommendation": {"phases": [{"phase": 1, "action": "x", "duration_days_range": "10-15"}]},
        "inference_mode": "mock",
    }
    report.update(overrides.get("report", {}))
    job_store.update(
        job.id,
        status="completed",
        report=report,
        prompt=overrides.get("prompt", "fake prompt text"),
    )
    return job.id


def test_feedback_unknown_job_returns_404():
    r = client.post("/api/jobs/does-not-exist/feedback", json={"rating": "up"})
    assert r.status_code == 404


def test_feedback_not_ready_returns_409():
    job = job_store.create(repo_path="x", language="fr", team_size=8, hourly_rate=80.0)
    r = client.post(f"/api/jobs/{job.id}/feedback", json={"rating": "up"})
    assert r.status_code == 409


def test_feedback_submission_persists_prompt_and_output(tmp_path, monkeypatch):
    from api import config as config_module

    feedback_path = tmp_path / "collected_feedback.jsonl"
    monkeypatch.setattr(config_module.settings, "archx_feedback_path", feedback_path)

    job_id = _make_completed_job()
    r = client.post(f"/api/jobs/{job_id}/feedback", json={"rating": "down", "correction": "wrong stack"})

    assert r.status_code == 200
    assert r.json() == {"ok": True}

    lines = feedback_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["job_id"] == job_id
    assert record["rating"] == "down"
    assert record["correction"] == "wrong stack"
    assert record["prompt"] == "fake prompt text"
    assert record["inference_mode"] == "mock"


def test_migration_targets_unknown_job_returns_404():
    r = client.get("/api/jobs/does-not-exist/migration-targets")
    assert r.status_code == 404


def test_migration_targets_returns_real_signals():
    job_id = _make_completed_job()
    r = client.get(f"/api/jobs/{job_id}/migration-targets")

    assert r.status_code == 200
    data = r.json()
    assert data["current_stack"] == "Django"
    assert "Go" in data["available_stacks"]
    # High coupling (8.0) should push Go into the suggestions.
    assert "Go" in data["suggested_stacks"]


def test_simulate_migration_matches_direct_cost_calculator_call():
    from architect_insight.metrics.cost_calculator import compute_full_report, cost_report_to_dict

    job_id = _make_completed_job()
    r = client.post(f"/api/jobs/{job_id}/simulate-migration", json={"target_stack": "Go"})
    assert r.status_code == 200
    data = r.json()

    from api.services.pipeline import derive_duration_days

    duration_days = derive_duration_days([{"phase": 1, "action": "x", "duration_days_range": "10-15"}])
    expected = cost_report_to_dict(
        compute_full_report(
            current_stack="Django",
            target_stack="Go",
            duration_days=duration_days,
            team_size=8,
            current_cloud_cost=None,
            scale="medium",
            hourly_rate=80.0,
        )
    )
    assert data["migration_cost"] == expected["migration_cost"]
    assert data["current_cloud_cost"] == expected["current_cloud_cost"]
    assert data["target_cloud_cost"] == expected["target_cloud_cost"]
    assert data["monthly_savings"] == expected["monthly_savings"]


def test_simulate_migration_same_stack_has_null_payback():
    job_id = _make_completed_job()
    r = client.post(f"/api/jobs/{job_id}/simulate-migration", json={"target_stack": "Django"})
    assert r.status_code == 200
    assert r.json()["payback_months"] is None
