"""Analysis job creation and background execution."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.config import settings
from api.schemas import AnalyzeRequest, AnalyzeResponse, JobStatus
from api.services.job_store import job_store
from api.services.pipeline import run_pipeline
from api.services.repo_resolver import resolve_repo_path

router = APIRouter(tags=["analyze"])

STATUS_BY_STEP: dict[int, JobStatus] = {
    1: "collecting",
    2: "building_prompt",
    3: "inferring",
    4: "computing_costs",
}


def _run_job(job_id: str) -> None:
    job = job_store.get(job_id)
    if not job:
        return

    try:
        def on_progress(label: str, step: int) -> None:
            status = STATUS_BY_STEP.get(step, "computing_costs")
            job_store.update(job_id, status=status, step=step, step_label=label)

        report = run_pipeline(
            job.repo_path,
            language=job.language,
            mock=settings.use_mock_inference,
            model_path=settings.archx_model_path,
            team_size=job.team_size,
            hourly_rate=job.hourly_rate,
            on_progress=on_progress,
        )

        job_store.update(
            job_id,
            status="completed",
            step=5,
            step_label="Finalizing report",
            report=report,
        )
    except Exception as exc:
        job_store.update(
            job_id,
            status="failed",
            error=str(exc),
            step_label="Failed",
        )


@router.post("/api/analyze", response_model=AnalyzeResponse)
def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> AnalyzeResponse:
    try:
        resolved = resolve_repo_path(request.repo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = job_store.create(
        repo_path=str(resolved),
        language=request.language,
        team_size=request.team_size,
        hourly_rate=request.hourly_rate,
    )

    background_tasks.add_task(_run_job, job.id)
    return AnalyzeResponse(job_id=job.id)
