#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "============================================"
echo "  Dev Boss — bringing up backend + database"
echo "============================================"
echo ""

docker compose up --build -d postgres backend

echo ""
echo "============================================"
echo "  Backend:  http://localhost:${BACKEND_PORT:-8000}"
echo "  API docs: http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
echo "  To start the frontend (with hot reload):"
echo "    cd frontend && npm run dev"
echo "============================================"
echo ""
