"""Analysis job creation and background execution."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.config import settings
from api.schemas import AnalyzeRequest, AnalyzeResponse, JobStatus
from api.services.github_cloner import cleanup_clone, clone_repo, is_github_url
from api.services.job_store import job_store
from api.services.pipeline import run_pipeline
from api.services.repo_resolver import resolve_repo_path

router = APIRouter(tags=["analyze"])

STATUS_BY_STEP: dict[int, JobStatus] = {
    0: "cloning",
    1: "collecting",
    2: "building_prompt",
    3: "inferring",
    4: "computing_costs",
}


def _run_job(job_id: str) -> None:
    job = job_store.get(job_id)
    if not job:
        return

    clone_path: Path | None = None

    try:
        if is_github_url(job.repo_path):
            job_store.update(
                job_id,
                status="cloning",
                step=0,
                step_label="Cloning repository",
            )
            clone_path = clone_repo(job.repo_path, job_id)
            scan_path = str(clone_path)
        else:
            scan_path = job.repo_path

        def on_progress(label: str, step: int) -> None:
            status = STATUS_BY_STEP.get(step, "computing_costs")
            job_store.update(job_id, status=status, step=step, step_label=label)

        report = run_pipeline(
            scan_path,
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
    finally:
        if clone_path is not None:
            cleanup_clone(clone_path)


@router.post("/api/analyze", response_model=AnalyzeResponse)
def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> AnalyzeResponse:
    repo_input = request.repo.strip()

    if is_github_url(repo_input):
        stored_repo = repo_input
    else:
        try:
            stored_repo = str(resolve_repo_path(repo_input))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = job_store.create(
        repo_path=stored_repo,
        language=request.language,
        team_size=request.team_size,
        hourly_rate=request.hourly_rate,
    )

    background_tasks.add_task(_run_job, job.id)
    return AnalyzeResponse(job_id=job.id)
