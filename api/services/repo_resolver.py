"""Resolve repo slugs and paths to validated local directories."""

from __future__ import annotations

from pathlib import Path

from api.config import PROJECT_ROOT, settings
from api.services.github_cloner import is_github_url

DEMO_PROJECTS: dict[str, str] = {
    "django_app": "Django App",
    "springboot_app": "Spring Boot App",
    "flutter_app": "Flutter App",
}


def list_demo_projects() -> list[dict[str, str]]:
    projects = []
    for slug, label in DEMO_PROJECTS.items():
        path = settings.demo_projects_dir / slug
        if path.is_dir():
            projects.append({
                "slug": slug,
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "label": label,
            })
    return projects


def resolve_repo_path(repo: str) -> Path:
    repo = repo.strip()

    if is_github_url(repo):
        raise ValueError("GitHub URLs are cloned at runtime; pass the URL directly to /api/analyze")

    if repo in DEMO_PROJECTS:
        resolved = settings.demo_projects_dir / repo
    elif repo.startswith("demo_projects/"):
        resolved = PROJECT_ROOT / repo
    else:
        candidate = Path(repo)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / repo
        resolved = candidate.resolve()

    if ".." in resolved.parts:
        raise ValueError("Path traversal is not allowed")

    if not resolved.is_dir():
        raise ValueError(f"Repository not found: {repo}")

    return resolved
