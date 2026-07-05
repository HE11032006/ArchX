"""
database.py
-------------
Détecte la base de données utilisée par le projet en analysant :
- Les fichiers de configuration
- Les ORM utilisés
- Les migrations
- Une estimation de la complexité
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

# Mapping des fichiers de config vers les SGBD
DB_SIGNALS = {
    "postgresql": {
        "patterns": ["postgresql", "postgres", "psycopg2", "pg_", "5432"],
        "files": ["postgresql.conf", "pg_hba.conf"]
    },
    "mysql": {
        "patterns": ["mysql", "mariadb", "pymysql", "3306"],
        "files": ["my.cnf", "my.ini"]
    },
    "mongodb": {
        "patterns": ["mongodb", "pymongo", "mongoose", "27017"],
        "files": ["mongod.conf"]
    },
    "sqlite": {
        "patterns": ["sqlite", "sqlite3"],
        "files": ["*.db", "*.sqlite"]
    },
    "redis": {
        "patterns": ["redis", "6379"],
        "files": ["redis.conf"]
    },
    "dynamodb": {
        "patterns": ["dynamodb", "boto3.dynamodb"],
        "files": []
    }
}

ORM_SIGNALS = {
    "django_orm": ["django.db"],
    "sqlalchemy": ["sqlalchemy"],
    "hibernate": ["org.hibernate", "javax.persistence"],
    "typeorm": ["typeorm"],
    "prisma": ["@prisma/client"],
    "mongoose": ["mongoose"],
    "sequelize": ["sequelize"],
    "peewee": ["peewee"]
}


def detect_database(repo_path: str) -> dict:
    """
    Analyse le dépôt pour détecter la base de données utilisée.
    """
    repo_path = os.path.abspath(repo_path)
    detected_dbs = set()
    detected_orms = set()
    migration_count = 0
    config_files = []
    
    for root, dirs, files in os.walk(repo_path):
        # Ignorer les dossiers inutiles
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__"}]
        
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, repo_path)
            
            # Détection des fichiers de migration
            if "migration" in rel_path.lower() or "migrate" in rel_path.lower():
                migration_count += 1
            
            # Détection des fichiers de config
            for db_name, signals in DB_SIGNALS.items():
                for signal in signals:
                    if signal in rel_path.lower():
                        detected_dbs.add(db_name)
                        if "conf" in rel_path.lower() or "config" in rel_path.lower():
                            config_files.append(rel_path)
            
            # Détection des ORM dans le code
            if file.endswith(".py"):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for orm_name, patterns in ORM_SIGNALS.items():
                            for pattern in patterns:
                                if pattern in content:
                                    detected_orms.add(orm_name)
                except Exception:
                    pass
    
    # Si rien n'est détecté, on essaie de trouver des indices dans les dépendances
    if not detected_dbs:
        # Chercher les fichiers de dépendances
        for root, dirs, files in os.walk(repo_path):
            if "requirements.txt" in files:
                try:
                    with open(os.path.join(root, "requirements.txt"), "r") as f:
                        content = f.read()
                        for db_name, signals in DB_SIGNALS.items():
                            for pattern in signals["patterns"]:
                                if pattern in content:
                                    detected_dbs.add(db_name)
                except Exception:
                    pass
            if "package.json" in files:
                try:
                    import json
                    with open(os.path.join(root, "package.json"), "r") as f:
                        data = json.load(f)
                        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        for db_name, signals in DB_SIGNALS.items():
                            for pattern in signals["patterns"]:
                                if any(pattern in dep for dep in deps):
                                    detected_dbs.add(db_name)
                except Exception:
                    pass
    
    # Estimation de la complexité basée sur le nombre de migrations
    if migration_count > 50:
        complexity = "high"
    elif migration_count > 20:
        complexity = "medium"
    elif migration_count > 5:
        complexity = "low"
    else:
        complexity = "very_low"
    
    return {
        "detected_databases": list(detected_dbs) if detected_dbs else ["Non détecté"],
        "detected_orms": list(detected_orms) if detected_orms else ["Non détecté"],
        "migration_count": migration_count,
        "complexity": complexity,
        "config_files": config_files[:10],
        "has_database": bool(detected_dbs or migration_count)
    }