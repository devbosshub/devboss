# Dev Boss

- Website: [https://www.devboss.xyz/](https://www.devboss.xyz/)
- YouTube Intro: [https://youtu.be/cHeKkuT0XBQ](https://youtu.be/cHeKkuT0XBQ)

Dev Boss is an MVP platform for running an AI engineering team through a single dashboard. It manages projects, tasks, engineers, task runs, comments, approvals, and deployment handoffs across a full software delivery workflow.

This repository contains:

- `backend/` FastAPI API, orchestration logic, workflow state machine, storage, and tests
- `frontend/` Next.js dashboard UI
- `runtime/` Dockerized engineer runtime that runs Codex and sends heartbeats back to the backend
- `docker-compose.yml` local development stack with PostgreSQL

## What You Need

Before starting Dev Boss locally, make sure you have:

- Docker Desktop with Docker Compose enabled
- Node.js and npm if you want to run the frontend outside Docker
- Python 3.11+ if you want to run backend tests locally
- A GitHub personal access token with repo access
- A Codex auth JSON payload for the runtime, usually from `~/.codex/auth.json`

Optional for deployment testing:

- AWS credentials with access to your target S3 bucket and CloudFront distribution

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/devbosshub/devboss.git
cd devboss
```

### 2. Create the local environment file

Copy the example env file:

```bash
cp .env.example .env
```

The defaults are already usable for local development. The key values are:

```env
POSTGRES_DB=devboss
POSTGRES_USER=devboss
POSTGRES_PASSWORD=devboss
POSTGRES_PORT=5432

BACKEND_PORT=8000
FRONTEND_PORT=3000

DATABASE_URL=postgresql+psycopg://devboss:devboss@postgres:5432/devboss
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
UPLOAD_DIR=uploads
```

### 3. Start the stack

```bash
docker compose up --build -d
```

This starts:

- PostgreSQL on `localhost:5432`
- FastAPI backend on `http://localhost:8000`
- Next.js frontend on `http://localhost:3000`

### 4. Open the app

- UI: [http://localhost:3000](http://localhost:3000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## First-Time App Setup

After the app is running, open `Global Configs` in the UI and add the required configuration entries.

### Required Global Configs

These are the minimum configs needed for engineers to launch and work on tasks:

#### `codex_auth_json`

This should be the full contents of your local Codex auth file.

Example source on your machine:

```bash
cat ~/.codex/auth.json
```

Copy the full JSON content and paste it into the `codex_auth_json` global config value.

#### `github_developer_token`

This should be a GitHub token with permission to:

- clone private repositories if needed
- push branches
- create pull requests

### Optional Global Configs

Add these if you want to test deployment flows that use AWS:

#### `aws_access_key_id`
#### `aws_secret_access_key`
#### `aws_region`

These are injected into the engineer runtime container during deployment-stage work.

## Creating Your First Project

From the `Projects` page:

1. Click `Add Project`
2. Enter the project name
3. Add the GitHub repository URL
4. Set the default branch, for example `main`
5. Add deployment config JSON if you want deployment support
6. Add deployment instructions if the project has specific deploy steps

### Example deployment config

```json
{
  "type": "frontend_static_s3",
  "build_command": "npm run build",
  "output_dir": "out",
  "s3_bucket": "my-site-bucket",
  "cloudfront_distribution_id": "E1234567890",
  "aws_region": "ap-south-1"
}
```

### Example deployment instructions

```md
Build the frontend using `npm run build`.

Upload the files from the `out/` directory to the configured S3 bucket.

After upload succeeds, invalidate the configured CloudFront distribution and include the invalidation id in the deployment summary.
```

## Creating Engineers

From the `Engineers` page:

1. Click `Add New Engineer`
2. Fill in the engineer profile
3. Save the engineer
4. Click `Start` in the engineer table to launch the runtime container

When started, an engineer:

- launches a Docker container
- writes the configured Codex auth JSON into `/root/.codex/auth.json`
- sends heartbeat pings back to the backend
- polls for work when assigned tasks are in runnable AI stages

## Creating Tasks

From a project dashboard:

1. Click `Create Task`
2. Select the project
3. Assign the task to an engineer
4. Fill in the requirements
5. Save the task in `Draft`

Default task values are prefilled for:

- Acceptance criteria
- Implementation steps

## Workflow Stages

Dev Boss currently uses these stages:

- `Draft`
- `AI Grooming`
- `Ready for Build`
- `In Progress`
- `AI Testing`
- `Human Testing`
- `Ready to Deploy`
- `Deployment`
- `Archived`

### What they mean

#### Draft

Human writes the task requirements.

#### AI Grooming

Codex inspects the task and repository, identifies gaps, and decides whether the task is implementation-ready.

#### Ready for Build

Human confirms the task is ready for implementation.

#### In Progress

The engineer implements the task on a task branch and prepares it for the next phase.

#### AI Testing

Codex validates the branch, runs checks, and reports issues or success.

#### Human Testing

Human reviews the outcome and confirms behavior before PR/deployment preparation.

#### Ready to Deploy

Codex prepares the pull request and final release handoff. Human still controls when to move into actual deployment.

#### Deployment

Codex deploys from the project default branch using project deployment config and deployment instructions.

#### Archived

The task is complete and no longer shown in the default working board.

## How Engineers Work

When an engineer claims a task, Dev Boss prepares a task bundle for Codex containing:

- `TASK.md`
- `COMMENTS.md`
- `PROJECT_CONTEXT.md`
- `STAGE_INSTRUCTIONS.md`

The stage instructions come from markdown prompt files in:

- `backend/app/prompts/ai_grooming.md`
- `backend/app/prompts/in_progress.md`
- `backend/app/prompts/ai_testing.md`
- `backend/app/prompts/ready_to_deploy.md`
- `backend/app/prompts/deployment.md`

These prompts are global across projects. Project-specific behavior is supplied through:

- engineer skill markdown
- project deployment config
- project deployment instructions

## Running Tests

### Backend tests

If you want to run backend tests locally:

```bash
.venv/bin/pytest backend/tests
```

### Frontend production build

```bash
cd frontend
npm run build
```

## Common Local Commands

Start the stack:

```bash
docker compose up --build -d
```

Stop the stack:

```bash
docker compose down
```

View running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

## Notes and Assumptions

- PostgreSQL schema is initialized automatically on backend startup
- The current schema flow is model-driven with startup patching, not full Alembic migrations yet
- Engineer runtime containers are launched separately by the backend and are not part of the main Compose services
- Global Configs are stored in the application database
- Secret values are masked in the UI, but you should still treat the local database as sensitive
- This is still an MVP and some deployment behavior is prompt-driven rather than fully deterministic adapter code

## Recommended First End-to-End Test

1. Start the stack
2. Add `codex_auth_json`
3. Add `github_developer_token`
4. Create an engineer and start it
5. Create a project with a GitHub repo
6. Create a task and assign it to that engineer
7. Move the task into `AI Grooming`
8. Watch task comments and task runs from the task page

## More Documentation

There is also an in-app `Usage Guide` page linked from the left navigation that explains the product modules and workflow in more detail.
