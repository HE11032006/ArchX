"""Demo projects listing endpoint."""

from fastapi import APIRouter

from api.schemas import DemoProject
from api.services.repo_resolver import list_demo_projects

router = APIRouter(tags=["demo-projects"])


@router.get("/api/demo-projects", response_model=list[DemoProject])
def get_demo_projects() -> list[DemoProject]:
    return [DemoProject(**p) for p in list_demo_projects()]
