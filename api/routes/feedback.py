"""Human feedback (rating + optional correction) on a completed report."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from api.schemas import FeedbackRequest, FeedbackResponse
from api.services.feedback_store import append_feedback
from api.services.job_store import job_store

router = APIRouter(tags=["feedback"])


@router.post("/api/jobs/{job_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(job_id: str, request: FeedbackRequest) -> FeedbackResponse:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.report:
        raise HTTPException(status_code=409, detail="Report not ready")

    record = {
        "id": str(uuid.uuid4()),
        "job_id": job_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rating": request.rating,
        "correction": request.correction,
        "language": job.language,
        # Exact model input/output, so this record is directly usable to
        # reconstruct a (prompt, output) training pair for a future fine-tune
        # without cross-referencing other logs.
        "prompt": job.prompt,
        "model_output": job.report.get("recommendation"),
        # "mock" feedback should be filtered out of any future retraining set.
        "inference_mode": job.report.get("inference_mode"),
    }
    append_feedback(record)
    return FeedbackResponse(ok=True)
