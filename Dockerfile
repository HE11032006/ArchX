# syntax=docker/dockerfile:1
#
# ArchX — conteneur unique : frontend Next.js + backend FastAPI + modèle GGUF.
# Le navigateur ne parle qu'au port 3000 (Next.js) ; le frontend proxy ses
# appels /api/* vers le backend en interne (127.0.0.1:8000, jamais exposé) —
# voir frontend/next.config.ts::rewrites. Aucun CORS, aucune URL de tunnel à
# maintenir à jour, contrairement au déploiement Vercel + cloudflared.
#
# Build (repo GGUF PUBLIC, aucun token nécessaire) :
#   docker build -t archx-all-in-one .
#
# Build avec offload GPU (exemple CUDA) :
#   docker build --build-arg CMAKE_ARGS="-DGGML_CUDA=on" -t archx-all-in-one .
#
# Run :
#   docker run -p 3000:3000 archx-all-in-one
#
# Si le repo GGUF doit être privé, voir la variante --secret documentée dans
# l'historique du projet (stage model-downloader, même principe qu'avant).

ARG HF_MODEL_REPO="Karmelkke/archx-gemma4-12b-gguf"
ARG HF_MODEL_FILE="archx-gemma4-Q4_K_M.gguf"

# ---------- Stage 1 : téléchargement du modèle (jetable) ----------
FROM python:3.11-slim AS model-downloader
ARG HF_MODEL_REPO
ARG HF_MODEL_FILE
RUN pip install --no-cache-dir "huggingface_hub[cli]"
WORKDIR /model
RUN huggingface-cli download ${HF_MODEL_REPO} ${HF_MODEL_FILE} --local-dir /model

# ---------- Stage 2 : dépendances Python de serving (jetable) ----------
FROM python:3.11-slim AS python-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-serving.txt .
ARG CMAKE_ARGS=""
ENV CMAKE_ARGS=${CMAKE_ARGS}
RUN pip install --no-cache-dir --prefix=/install -r requirements-serving.txt

# ---------- Stage 3 : build du frontend Next.js (jetable) ----------
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Vide (pas absente) -> shared/api/client.ts utilise des chemins relatifs,
# interceptés par le rewrite Next.js vers le backend interne.
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build

# ---------- Stage 4 : runtime final (l'image réellement livrée) ----------
FROM python:3.11-slim
ARG HF_MODEL_FILE="archx-gemma4-Q4_K_M.gguf"

# Node.js pour exécuter le serveur Next.js standalone à côté du backend Python.
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y curl gnupg \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Backend ---
COPY --from=python-builder /install /usr/local
COPY --from=model-downloader /model/${HF_MODEL_FILE} ./model.gguf
COPY api/ ./api/
COPY architect_insight/ ./architect_insight/
COPY training/format_for_training.py ./training/format_for_training.py
ENV ARCHX_MODEL_PATH=/app/model.gguf

# --- Frontend (sortie "standalone" — pas de node_modules complet copié) ---
COPY --from=frontend-builder /app/.next/standalone ./frontend/
COPY --from=frontend-builder /app/.next/static ./frontend/.next/static
COPY --from=frontend-builder /app/public ./frontend/public

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 3000
# CORS_ORIGINS reste sans effet utile ici (appels internes same-origin via le
# proxy) mais peut être passé à `docker run -e` si besoin d'un accès direct
# au port 8000 pour du debug — jamais codé en dur dans l'image.
CMD ["./docker-entrypoint.sh"]
