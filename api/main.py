"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routes import analyze, demo_projects, feedback, health, jobs, simulate

app = FastAPI(title="ArchX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(demo_projects.router)
app.include_router(analyze.router)
app.include_router(jobs.router)
app.include_router(feedback.router)
app.include_router(simulate.router)
