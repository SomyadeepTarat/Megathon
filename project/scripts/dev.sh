#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -x .venv/bin/python || ! -d frontend/node_modules ]]; then
  echo "Install the Python and frontend dependencies using README.md first." >&2
  exit 1
fi

backend_pid=''
frontend_pid=''
cleanup() {
  [[ -z "$frontend_pid" ]] || kill "$frontend_pid" 2>/dev/null || true
  [[ -z "$backend_pid" ]] || kill "$backend_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# Reuse an already running backend, otherwise start the prepared demo service.
if ! curl --fail --silent http://127.0.0.1:8001/health >/dev/null; then
  GREENPRINT_PROPERTY_DATASET="${GREENPRINT_PROPERTY_DATASET:-demo}" \
    .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001 &
  backend_pid=$!
  ready=false
  for ((attempt=0; attempt<30; attempt++)); do
    if curl --fail --silent http://127.0.0.1:8001/health >/dev/null; then
      ready=true
      break
    fi
    kill -0 "$backend_pid" 2>/dev/null || exit 1
    sleep 1
  done
  if [[ "$ready" != true ]]; then
    echo "The assessment backend did not become ready on port 8001." >&2
    exit 1
  fi
fi

echo "Kew: http://127.0.0.1:3000 — assessment backend ready."
GREENPRINT_BACKEND_URL=http://127.0.0.1:8001 npm --prefix frontend run dev -- --port 3000 &
frontend_pid=$!
wait "$frontend_pid"
