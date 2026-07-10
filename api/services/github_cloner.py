"""Clone public GitHub repositories into a temporary directory for analysis."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from api.config import settings

GITHUB_HOST = "github.com"
_SSH_PATTERN = re.compile(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$", re.IGNORECASE)
_SEGMENT_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def is_github_url(repo: str) -> bool:
    repo = repo.strip()
    if _SSH_PATTERN.match(repo):
        return True
    lower = repo.lower()
    if lower.startswith("github.com/") or f"{GITHUB_HOST}/" in lower:
        return True
    parsed = urlparse(repo if "://" in repo else f"https://{repo}")
    host = parsed.netloc.lower().removeprefix("www.")
    return host == GITHUB_HOST and len(parsed.path.strip("/").split("/")) >= 2


def _validate_segment(name: str, label: str) -> None:
    if not name or ".." in name or not _SEGMENT_PATTERN.match(name):
        raise ValueError(f"Invalid GitHub {label}: {name}")


def _parse_github_repo(repo: str) -> tuple[str, str]:
    repo = repo.strip().rstrip("/")

    ssh_match = _SSH_PATTERN.match(repo)
    if ssh_match:
        owner, name = ssh_match.group(1), ssh_match.group(2)
        _validate_segment(owner, "owner")
        _validate_segment(name, "repository")
        return owner, name

    normalized = repo if "://" in repo else f"https://{repo.removeprefix('/')}"
    parsed = urlparse(normalized)
    host = parsed.netloc.lower().removeprefix("www.")
    if host != GITHUB_HOST:
        raise ValueError(f"Only {GITHUB_HOST} URLs are supported")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL: expected owner/repository")

    owner, name = parts[0], parts[1]
    if name.endswith(".git"):
        name = name[:-4]

    _validate_segment(owner, "owner")
    _validate_segment(name, "repository")
    return owner, name


def normalize_github_url(repo: str) -> str:
    owner, name = _parse_github_repo(repo)
    return f"https://{GITHUB_HOST}/{owner}/{name}.git"


def clone_repo(url: str, job_id: str) -> Path:
    clone_url = normalize_github_url(url)
    base_dir = settings.clone_dir.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    dest = (base_dir / job_id).resolve()
    if dest != base_dir and base_dir not in dest.parents:
        raise ValueError("Invalid clone destination")

    if dest.exists():
        cleanup_clone(dest)

    cmd = [
        "git",
        "clone",
        "--single-branch",
        f"--depth={settings.clone_depth}",
        clone_url,
        str(dest),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.clone_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        cleanup_clone(dest)
        raise ValueError(
            f"Git clone timed out after {settings.clone_timeout}s"
        ) from exc
    except FileNotFoundError as exc:
        cleanup_clone(dest)
        raise ValueError("git is not installed or not available in PATH") from exc

    if result.returncode != 0:
        cleanup_clone(dest)
        stderr = (result.stderr or result.stdout or "").strip()
        raise ValueError(f"Git clone failed: {stderr or 'unknown error'}")

    if not dest.is_dir():
        cleanup_clone(dest)
        raise ValueError("Git clone failed: destination directory was not created")

    return dest


def cleanup_clone(path: Path) -> None:
    if not path.exists():
        return

    def _handle_remove_error(func, target: str, exc_info) -> None:
        if not os.access(target, os.W_OK):
            os.chmod(target, stat.S_IWUSR | stat.S_IREAD)
            func(target)
            return
        raise exc_info[1]

    try:
        shutil.rmtree(path, onerror=_handle_remove_error)
    except OSError:
        shutil.rmtree(path, ignore_errors=True)
