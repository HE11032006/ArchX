"""Thread-safe in-memory job store."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from api.schemas import JobStatus


@dataclass
class Job:
    id: str
    status: JobStatus = "queued"
    step: int = 0
    step_label: str = "Queued"
    error: str | None = None
    report: dict[str, Any] | None = None
    repo_path: str = ""
    language: str = "fr"
    team_size: int = 8
    hourly_rate: float = 80.0


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(
        self,
        *,
        repo_path: str,
        language: str,
        team_size: int,
        hourly_rate: float,
    ) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            repo_path=repo_path,
            language=language,
            team_size=team_size,
            hourly_rate=hourly_rate,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        step: int | None = None,
        step_label: str | None = None,
        error: str | None = None,
        report: dict | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if status is not None:
                job.status = status
            if step is not None:
                job.step = step
            if step_label is not None:
                job.step_label = step_label
            if error is not None:
                job.error = error
            if report is not None:
                job.report = report


job_store = JobStore()
