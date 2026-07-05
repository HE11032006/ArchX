"""
performance.py
----------------
Détecte les indicateurs de performance potentiels :
- Endpoints critiques
- Appels à des services externes
- Boucles et requêtes N+1 potentielles
- Utilisation de cache
- Async
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

# Patterns pour détecter les endpoints
ENDPOINT_PATTERNS = [
    (r'@(app|router|route|get|post|put|delete|patch)\(["\'](/[^"\']*)["\']', "FastAPI/Flask"),
    (r'@RequestMapping\(["\']([^"\']*)["\']', "Spring"),
    (r'app\.(get|post|put|delete|patch)\(["\'](/[^"\']*)["\']', "Express"),
]

# Patterns pour détecter les appels externes
EXTERNAL_CALL_PATTERNS = [
    r'(requests\.|urllib\.|httpx\.|aiohttp\.|fetch\(|axios\.|http\.Client)',
    r'(database|db|prisma\.|model\.|query|select|insert|update|delete)',
    r'(redis\.|cache\.|memcache\.|invalidate)',
    r'(kafka\.|rabbitmq\.|publish|consume|subscribe)',
]


def detect_performance(repo_path: str) -> dict:
    """
    Analyse le dépôt pour détecter des indicateurs de performance.
    """
    repo_path = os.path.abspath(repo_path)
    endpoints = []
    external_calls = 0
    cached_operations = 0
    async_operations = 0
    potential_n_plus_1 = 0
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "target"}]
        
        for file in files:
            if not file.endswith((".py", ".js", ".ts", ".java", ".dart", ".go")):
                continue
            
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, repo_path)
            
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    # Détection des endpoints
                    for pattern, framework in ENDPOINT_PATTERNS:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if isinstance(match, tuple):
                                path = match[-1]
                            else:
                                path = match
                            endpoints.append({
                                "path": path,
                                "framework": framework,
                                "file": rel_path
                            })
                    
                    # Détection des appels externes
                    for pattern in EXTERNAL_CALL_PATTERNS:
                        external_calls += len(re.findall(pattern, content, re.IGNORECASE))
                    
                    # Détection du cache
                    cache_patterns = [r'(cache\.|cached|@cached|redis\.|memcache\.)']
                    for pattern in cache_patterns:
                        cached_operations += len(re.findall(pattern, content, re.IGNORECASE))
                    
                    # Détection de l'async
                    async_patterns = [r'\basync\b', r'await\b', r'asyncio\.', r'Future\.', r'async/await']
                    for pattern in async_patterns:
                        async_operations += len(re.findall(pattern, content, re.IGNORECASE))
                    
                    # Détection de N+1 (indices : query dans une boucle)
                    if "for" in content.lower() and ("query" in content.lower() or "select" in content.lower()):
                        potential_n_plus_1 += 1
            except Exception:
                continue
    
    # Limiter les endpoints affichés
    endpoints = endpoints[:20]
    
    # Évaluer le niveau de performance
    if external_calls > 100 and cached_operations < 10:
        performance_score = "medium"
    elif external_calls > 200:
        performance_score = "low"
    elif cached_operations > 50:
        performance_score = "high"
    else:
        performance_score = "medium"
    
    return {
        "endpoints_count": len(endpoints),
        "endpoints": endpoints[:10],
        "external_calls_detected": external_calls,
        "cached_operations_detected": cached_operations,
        "async_operations_detected": async_operations,
        "potential_n_plus_1_hotspots": potential_n_plus_1,
        "performance_score": performance_score,
        "has_async": async_operations > 0,
        "has_cache": cached_operations > 0,
    }