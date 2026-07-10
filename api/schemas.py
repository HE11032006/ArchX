"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

JobStatus = Literal[
    "queued",
    "collecting",
    "building_prompt",
    "inferring",
    "computing_costs",
    "completed",
    "failed",
]


class AnalyzeRequest(BaseModel):
    repo: str = Field(..., min_length=1, description="Demo slug, relative or absolute repo path")
    language: Literal["fr", "en"] = "fr"
    team_size: int = Field(default=8, ge=1, le=100)
    hourly_rate: float = Field(default=80.0, ge=0)


class AnalyzeResponse(BaseModel):
    job_id: str


class DemoProject(BaseModel):
    slug: str
    path: str
    label: str


class JobResponse(BaseModel):
    id: str
    status: JobStatus
    step: int
    step_label: str
    error: str | None = None
    report: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
