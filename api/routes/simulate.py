"""Deterministic 'what if I migrate to stack X' simulator for a completed job.

No LLM call — reuses the exact same compute_full_report()/cost_report_to_dict()
already used to build the original report's cost_analysis, just with a
user-chosen target_stack instead of the single heuristic pick in
pipeline.py::run_pipeline.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import (
    MigrationTargetsResponse,
    SimulateMigrationRequest,
    SimulateMigrationResponse,
)
from api.services.job_store import job_store
from api.services.pipeline import derive_current_stack, derive_duration_days
from architect_insight.metrics.cost_calculator import (
    STACK_MONTHLY_COSTS,
    compute_full_report,
    cost_report_to_dict,
    suggest_target_stacks,
)

router = APIRouter(tags=["simulate"])


def _get_completed_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.report:
        raise HTTPException(status_code=409, detail="Report not ready")
    return job


@router.get("/api/jobs/{job_id}/migration-targets", response_model=MigrationTargetsResponse)
def get_migration_targets(job_id: str) -> MigrationTargetsResponse:
    job = _get_completed_job(job_id)
    metrics = job.report["metrics"]
    current_stack = derive_current_stack(metrics)
    suggested = suggest_target_stacks(
        current_stack,
        metrics.get("coupling_score", 0.0),
        metrics.get("cohesion_score", 0.0),
    )
    return MigrationTargetsResponse(
        current_stack=current_stack,
        available_stacks=list(STACK_MONTHLY_COSTS.keys()),
        suggested_stacks=suggested,
    )


@router.post("/api/jobs/{job_id}/simulate-migration", response_model=SimulateMigrationResponse)
def simulate_migration(job_id: str, request: SimulateMigrationRequest) -> SimulateMigrationResponse:
    job = _get_completed_job(job_id)
    metrics = job.report["metrics"]
    current_stack = derive_current_stack(metrics)
    duration_days = derive_duration_days(job.report["recommendation"].get("phases", []))
    team_size = request.team_size or job.team_size
    hourly_rate = request.hourly_rate or job.hourly_rate

    cost_report = compute_full_report(
        current_stack=current_stack,
        target_stack=request.target_stack,
        duration_days=duration_days,
        team_size=team_size,
        current_cloud_cost=None,
        scale=request.scale,
        hourly_rate=hourly_rate,
    )
    cost_data = cost_report_to_dict(cost_report)

    return SimulateMigrationResponse(
        current_stack=current_stack,
        target_stack=request.target_stack,
        migration_cost=cost_data["migration_cost"],
        current_cloud_cost=cost_data["current_cloud_cost"],
        target_cloud_cost=cost_data["target_cloud_cost"],
        monthly_savings=cost_data["monthly_savings"],
        payback_months=cost_data.get("payback_months", cost_data.get("roi_months", 0)),
        cost_confidence=cost_data["cost_confidence"],
    )
