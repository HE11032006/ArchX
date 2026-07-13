#!/bin/sh
set -e

# Backend FastAPI — port interne uniquement, jamais exposé hors du conteneur
# (le frontend le proxy via next.config.ts::rewrites).
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Si le backend meurt, on veut que tout le conteneur s'arrête plutôt que de
# tourner silencieusement avec un frontend qui ne peut plus rien servir.
trap "kill $BACKEND_PID 2>/dev/null" EXIT

# Frontend Next.js (standalone) — premier plan, PID 1 du conteneur, reçoit
# proprement les signaux d'arrêt (docker stop).
cd /app/frontend
exec node server.js
