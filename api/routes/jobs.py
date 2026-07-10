"""Job status endpoint."""

from fastapi import APIRouter, HTTPException

from api.schemas import JobResponse
from api.services.job_store import job_store

router = APIRouter(tags=["jobs"])

STATUS_BY_STEP = {
    1: "collecting",
    2: "building_prompt",
    3: "inferring",
    4: "computing_costs",
    5: "completed",
}


@router.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=job.id,
        status=job.status,
        step=job.step,
        step_label=job.step_label,
        error=job.error,
        report=job.report,
    )
