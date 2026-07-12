"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

JobStatus = Literal[
    "queued",
    "cloning",
    "collecting",
    "building_prompt",
    "inferring",
    "computing_costs",
    "completed",
    "failed",
]


class AnalyzeRequest(BaseModel):
    repo: str = Field(
        ...,
        min_length=1,
        description="GitHub URL, demo slug, or relative/absolute local repo path",
    )
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


class FeedbackRequest(BaseModel):
    rating: Literal["up", "down"]
    correction: str | None = Field(default=None, max_length=4000)


class FeedbackResponse(BaseModel):
    ok: bool = True


class SimulateMigrationRequest(BaseModel):
    target_stack: str
    team_size: int | None = Field(default=None, ge=1, le=100)
    hourly_rate: float | None = Field(default=None, ge=0)
    scale: Literal["small", "medium", "large"] = "medium"


class SimulateMigrationResponse(BaseModel):
    current_stack: str
    target_stack: str
    migration_cost: float
    current_cloud_cost: float
    target_cloud_cost: float
    monthly_savings: float
    payback_months: float
    cost_confidence: str


class MigrationTargetsResponse(BaseModel):
    current_stack: str
    available_stacks: list[str]
    suggested_stacks: list[str]
