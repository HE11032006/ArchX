"""
dependencies.py
-----------------
Analyse les fichiers de dépendances d'un projet pour identifier :
- Les langages et leurs dépendances
- Le nombre de dépendances
- Les versions (et si elles sont récentes ou obsolètes)
- Les vulnérabilités potentielles (via une API externe, optionnel)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from dataclasses import dataclass, field

# Mapping des fichiers de dépendances vers les langages
MANIFEST_TO_LANG = {
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "package.json": "JavaScript/TypeScript (Node)",
    "package-lock.json": "JavaScript/TypeScript (Node)",
    "yarn.lock": "JavaScript/TypeScript (Node)",
    "pnpm-lock.yaml": "JavaScript/TypeScript (Node)",
    "go.mod": "Go",
    "go.sum": "Go",
    "Cargo.toml": "Rust",
    "Cargo.lock": "Rust",
    "pubspec.yaml": "Dart/Flutter",
    "pubspec.lock": "Dart/Flutter",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "settings.gradle": "Java/Kotlin (Gradle)",
    "Gemfile": "Ruby",
    "Gemfile.lock": "Ruby",
    "composer.json": "PHP",
    "composer.lock": "PHP",
}

# Versions récentes connues (pour détection d'obsolescence)
RECENT_VERSIONS = {
    "python": {"min_major": 3, "min_minor": 11},
    "django": {"min_major": 4, "min_minor": 2},
    "fastapi": {"min_major": 0, "min_minor": 100},
    "flask": {"min_major": 2, "min_minor": 3},
    "spring-boot": {"min_major": 3, "min_minor": 0},
    "react": {"min_major": 18, "min_minor": 0},
    "vue": {"min_major": 3, "min_minor": 0},
    "angular": {"min_major": 17, "min_minor": 0},
    "flutter": {"min_major": 3, "min_minor": 16},
    "go": {"min_major": 1, "min_minor": 21},
    "rust": {"min_major": 1, "min_minor": 75},
}

@dataclass
class DependencyInfo:
    name: str
    version: str | None
    is_obsolete: bool
    latest_known: str | None
    type: str  # "production" ou "development"


@dataclass
class LanguageDependencies:
    language: str
    manifest_file: str
    count: int
    dependencies: list[DependencyInfo]
    obsolete_count: int
    dev_dependencies: list[DependencyInfo] = field(default_factory=list)


def _parse_requirements_txt(filepath: str) -> list[DependencyInfo]:
    """Parse un fichier requirements.txt"""
    deps = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # format: package==version ou package>=version ou package
            if "==" in line:
                name, version = line.split("==", 1)
                is_obsolete = _check_obsolete(name, version)
                deps.append(DependencyInfo(
                    name=name.strip(),
                    version=version.strip(),
                    is_obsolete=is_obsolete,
                    latest_known=_get_latest_version(name),
                    type="production"
                ))
            elif ">=" in line:
                name, version = line.split(">=", 1)
                deps.append(DependencyInfo(
                    name=name.strip(),
                    version=f">={version.strip()}",
                    is_obsolete=False,  # on ne peut pas savoir
                    latest_known=_get_latest_version(name),
                    type="production"
                ))
            else:
                deps.append(DependencyInfo(
                    name=line,
                    version=None,
                    is_obsolete=False,
                    latest_known=_get_latest_version(line),
                    type="production"
                ))
    return deps


def _parse_package_json(filepath: str) -> tuple[list[DependencyInfo], list[DependencyInfo]]:
    """Parse un fichier package.json"""
    import json
    deps = []
    dev_deps = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for name, version in data.get("dependencies", {}).items():
        is_obsolete = _check_obsolete(name, version)
        deps.append(DependencyInfo(
            name=name,
            version=version,
            is_obsolete=is_obsolete,
            latest_known=_get_latest_version(name),
            type="production"
        ))
    
    for name, version in data.get("devDependencies", {}).items():
        is_obsolete = _check_obsolete(name, version)
        dev_deps.append(DependencyInfo(
            name=name,
            version=version,
            is_obsolete=is_obsolete,
            latest_known=_get_latest_version(name),
            type="development"
        ))
    
    return deps, dev_deps


def _parse_go_mod(filepath: str) -> list[DependencyInfo]:
    """Parse un fichier go.mod"""
    deps = []
    in_require = False
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("require") and not in_require:
                in_require = True
                continue
            if in_require and line.startswith(")"):
                in_require = False
                continue
            if in_require:
                parts = line.split()
                if len(parts) >= 2:
                    name, version = parts[0], parts[1]
                    is_obsolete = _check_obsolete(name, version)
                    deps.append(DependencyInfo(
                        name=name,
                        version=version,
                        is_obsolete=is_obsolete,
                        latest_known=_get_latest_version(name),
                        type="production"
                    ))
    return deps


def _parse_pubspec_yaml(filepath: str) -> tuple[list[DependencyInfo], list[DependencyInfo]]:
    """Parse un fichier pubspec.yaml (Flutter)"""
    try:
        import yaml
    except ImportError:
        return [], []
    
    deps = []
    dev_deps = []
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    for name, version in data.get("dependencies", {}).items():
        if isinstance(version, dict):
            version = version.get("version", "unknown")
        is_obsolete = _check_obsolete(name, version)
        deps.append(DependencyInfo(
            name=name,
            version=version,
            is_obsolete=is_obsolete,
            latest_known=_get_latest_version(name),
            type="production"
        ))
    
    for name, version in data.get("dev_dependencies", {}).items():
        if isinstance(version, dict):
            version = version.get("version", "unknown")
        dev_deps.append(DependencyInfo(
            name=name,
            version=version,
            is_obsolete=False,
            latest_known=_get_latest_version(name),
            type="development"
        ))
    
    return deps, dev_deps


def _check_obsolete(name: str, version: str) -> bool:
    """Vérifie si une dépendance est obsolète."""
    name_lower = name.lower()
    for key, spec in RECENT_VERSIONS.items():
        if key in name_lower:
            # Extraction de la version majeure
            match = re.search(r'(\d+)\.', version)
            if match:
                major = int(match.group(1))
                if major < spec["min_major"]:
                    return True
            break
    return False


def _get_latest_version(name: str) -> str | None:
    """Retourne la version connue la plus récente (pour info)."""
    name_lower = name.lower()
    for key, spec in RECENT_VERSIONS.items():
        if key in name_lower:
            return f"{spec['min_major']}.{spec['min_minor']}+"
    return None


def analyze_dependencies(repo_path: str) -> dict:
    """
    Analyse les fichiers de dépendances dans le dépôt.
    """
    repo_path = os.path.abspath(repo_path)
    results = {}
    
    for root, dirs, files in os.walk(repo_path):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target"}]
        
        for file in files:
            filepath = os.path.join(root, file)
            lang = MANIFEST_TO_LANG.get(file)
            if not lang:
                continue
            
            deps = []
            dev_deps = []
            
            try:
                if file == "requirements.txt":
                    deps = _parse_requirements_txt(filepath)
                elif file == "package.json":
                    deps, dev_deps = _parse_package_json(filepath)
                elif file == "go.mod":
                    deps = _parse_go_mod(filepath)
                elif file == "pubspec.yaml":
                    deps, dev_deps = _parse_pubspec_yaml(filepath)
                elif file in ["pyproject.toml", "Cargo.toml", "pom.xml", "build.gradle", "composer.json", "Gemfile"]:
                    # Pour les autres fichiers, on compte juste le nombre de dépendances
                    # sans parsing détaillé (pour simplifier)
                    deps = [DependencyInfo(
                        name="Voir le fichier manifeste pour les détails",
                        version=None,
                        is_obsolete=False,
                        latest_known=None,
                        type="production"
                    )]
            except Exception:
                continue
            
            results[lang] = {
                "manifest_file": file,
                "count": len(deps),
                "obsolete_count": sum(1 for d in deps if d.is_obsolete),
                "dependencies": [
                    {
                        "name": d.name,
                        "version": d.version,
                        "is_obsolete": d.is_obsolete,
                        "latest_known": d.latest_known,
                        "type": d.type
                    }
                    for d in deps[:20]  # Limite à 20 pour ne pas surcharger
                ],
                "dev_dependencies": [
                    {
                        "name": d.name,
                        "version": d.version,
                        "type": d.type
                    }
                    for d in dev_deps[:10]
                ]
            }
    
    return {
        "total_dependencies": sum(r["count"] for r in results.values()),
        "total_obsolete": sum(r["obsolete_count"] for r in results.values()),
        "languages": results,
        "has_dependency_files": bool(results)
    }