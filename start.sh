#!/usr/bin/env bash
set -e

uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true &
FRONTEND_PID=$!

# Se qualquer um dos processos morrer, derruba o contêiner.
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait -n
