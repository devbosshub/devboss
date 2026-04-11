# Dev Boss

Dev Boss is an MVP platform for managing AI-assisted software delivery end to end. It includes:

- A `FastAPI` backend for projects, tasks, engineers, task runs, comments, artifacts, and agent polling
- A `Next.js` dashboard for board, project, engineer, and task management
- A Docker-based engineer runtime that polls for work and executes Codex-driven task runs
- `Docker Compose` for local development infrastructure, including PostgreSQL

## Monorepo layout

- `backend/` FastAPI API, orchestration logic, storage, and tests
- `frontend/` Next.js dashboard built with React and shadcn-style primitives
- `runtime/` engineer polling client and Docker image
- `docker-compose.yml` local development stack

## Quick start

1. Copy `.env.example` to `.env`.
2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

## Notes

- PostgreSQL runs in Docker Compose and persists data in a named volume.
- Backend startup runs database initialization automatically for the MVP.
- Artifacts are stored on the backend filesystem under `/app/uploads` in containers and `backend/uploads/` locally.

