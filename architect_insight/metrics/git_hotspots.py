"""
git_hotspots.py
-----------------
Utilise `git log` (déjà installé sur toute machine de dev, aucune dépendance
externe) pour identifier :
  - les fichiers modifiés le plus souvent (churn) sur une fenêtre de temps
  - les fichiers les plus souvent touchés par des commits "correctifs"
    (fix/bug/hotfix/patch dans le message de commit)

C'est un signal FACTUEL sur l'historique réel du projet — contrairement à un
score de "frustration d'équipe" qui nécessiterait des labels qui n'existent pas.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

_BUGFIX_PATTERN = re.compile(r"\b(fix|bug|hotfix|patch|error|crash|regression)\b", re.IGNORECASE)


@dataclass
class GitHotspot:
    path: str
    total_changes: int
    bugfix_changes: int

    @property
    def bugfix_ratio(self) -> float:
        return round(self.bugfix_changes / self.total_changes, 2) if self.total_changes else 0.0


def _run_git(repo_path: str, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", repo_path] + args,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def is_git_repo(repo_path: str) -> bool:
    return bool(_run_git(repo_path, ["rev-parse", "--is-inside-work-tree"]).strip())


def analyze_hotspots(repo_path: str, since: str = "12 months ago", top_n: int = 10) -> list[GitHotspot]:
    if not is_git_repo(repo_path):
        return []

    # Format: <hash>\x1f<message>\x1e puis liste de fichiers, séparés par \x1e entre commits
    log = _run_git(
        repo_path,
        [
            "log",
            f"--since={since}",
            "--name-only",
            "--pretty=format:__COMMIT__%x1f%s",
        ],
    )
    if not log:
        return []

    changes: dict[str, int] = {}
    bugfixes: dict[str, int] = {}

    current_is_bugfix = False
    for line in log.splitlines():
        if line.startswith("__COMMIT__"):
            message = line.split("\x1f", 1)[-1]
            current_is_bugfix = bool(_BUGFIX_PATTERN.search(message))
            continue
        path = line.strip()
        if not path:
            continue
        changes[path] = changes.get(path, 0) + 1
        if current_is_bugfix:
            bugfixes[path] = bugfixes.get(path, 0) + 1

    hotspots = [
        GitHotspot(path=p, total_changes=n, bugfix_changes=bugfixes.get(p, 0))
        for p, n in changes.items()
    ]
    hotspots.sort(key=lambda h: (h.bugfix_changes, h.total_changes), reverse=True)
    return hotspots[:top_n]
