export const usageGuideMarkdown = `
# Dev Boss Documentation

## Overview

Dev Boss is an AI-assisted software delivery platform. It orchestrates AI engineer agents to design, build, test, and deploy software across projects. Humans supervise the pipeline through approvals, code reviews, and strategy decisions.

### Architecture at a Glance

| Layer | Technology | Role |
|-------|-----------|------|
| Frontend | Next.js 16 (Static Export) | S3-hosted dashboard, Kanban board, PRD editor |
| Backend | FastAPI + SQLAlchemy | REST API, orchestration, state machine |
| Database | PostgreSQL 16 | All persistent state |
| Runtime | Docker containers | Isolated AI agents running Opencode CLI |
| AI Agent | Opencode + DeepSeek v4 Pro | Performs grooming, building, testing, deployment |
| Auth | External JWT service | Sign-in and token validation |

The frontend is built as a fully static site hosted on S3. It communicates exclusively with the backend API -- there is no server-side rendering.

---

## Core Concepts

### Organizations

Organizations are the top-level workspace grouping. They define access boundaries for projects, PRDs, tags, and members.

Each organization has:

- **name** and **slug** -- used for identification and routing
- **members** -- users with role-based access (admin, member)
- **projects** -- linked projects that inherit the org context
- **tags** -- org-scoped labels for filtering and categorization

Users are identified by email and authenticated via an external JWT service. When added to an organization, a user record is created if it doesn't already exist. Organization admins can add and remove members and manage roles.

### Projects

Projects are the delivery units. Each project maps to a Git repository and is tagged to one workflow.

A project stores:

- **name** and **repo_url** -- the codebase location
- **default_branch** -- typically \`main\` or \`master\`
- **workflow** -- which pipeline all tasks in this project follow
- **organization** -- which org owns this project
- **deploy_config** -- JSON blob for deployment configuration
- **deployment_instructions** -- free-form markdown for deploy context

The project board at \`/board?projectId=X\` is the primary monitoring surface. When a project is tagged to a workflow, the board renders stage columns. Tasks are automatically placed in the column matching their current workflow stage.

### Workflows

**Workflows are configurable delivery pipelines.** Instead of a fixed set of stages, you define your own to match any software delivery process.

A workflow has:

- **name** -- e.g. "Standard Web App Pipeline"
- **description** -- what this workflow is designed for
- **ordered stages** -- the pipeline sequence

Each **stage** in a workflow has:

| Property | Type | Description |
|----------|------|-------------|
| name | string | Display name, e.g. "AI Grooming" |
| stage_order | int | Position in the pipeline |
| assigned_engineer_id | FK | Which engineer picks up tasks at this stage |
| is_ai_executable | bool | Whether an AI runtime container executes this stage |
| requires_human_approval | bool | Pause task until a human approves |
| stage_instructions | markdown | Custom prompt telling the AI what to do at this stage |
| max_rework_attempts | int | Max failure loops before blocking (default: 3) |
| rework_target_stage_id | FK | Which stage to fall back to on failure |

The workflow editor at \`/workflows/edit?workflowId=X\` provides full control over all stage properties. Stages can be reordered using arrow buttons.

**Example workflow -- Standard SDLC Pipeline:**

| Order | Stage | Engineer | AI? | Approval? | Rework Target |
|-------|-------|----------|-----|-----------|---------------|
| 0 | AI Grooming | Backend Engineer | Yes | No | -- |
| 1 | Approval Gate | -- | No | Yes | -- |
| 2 | Build | Backend Engineer | Yes | No | Self (rework on same stage) |
| 3 | QA Testing | QA/Test Engineer | Yes | No | Build (falls back on failure) |
| 4 | Deploy | DevOps Engineer | Yes | Yes | Self |

### Engineers

Engineers are reusable AI worker profiles. Each engineer stores:

- **name** and **template** -- identity and specialization label
- **skill_markdown** -- tells the AI what expertise it has
- **model_provider** and **model_name** -- which LLM to use (default: DeepSeek/deepseek-v4-pro)
- **docker_image** -- container image for the runtime
- **poll_interval_seconds** -- how often the container checks for work

An engineer can be launched into multiple Docker containers. Each container sends heartbeats and polls for work in the stages it is assigned to. The engineers page shows real-time health status, runtime capacity, and busy/idle counts.

**Engineer assignment is per workflow stage**, not per task. When a task enters a stage, it automatically inherits that stage's engineer. Design your workflows by assigning the right engineer to each pipeline stage.

### PRDs -- Product Requirements Documents

PRDs capture feature requirements before they become tasks. The PRD flow is:

1. **Create** a PRD under an organization with a title and summary
2. **Chat** progressively with the AI to refine the body markdown
3. **Review** the final document
4. **Convert** to tasks -- select target projects and enter task titles (one per project)

A PRD has:

- **title** and **summary** -- high-level description
- **body_markdown** -- the full requirements document (editable)
- **status** -- draft -> in_review -> approved -> converted -> archived
- **comments** -- chat thread for progressive refinement
- **tags** -- linked tags for categorization

The PRD detail page at \`/prds/detail?prdId=X\` has a chat interface where you send messages to progressively build the document. The "Convert to Tasks" panel lets you select multiple projects and create matching tasks -- each task gets the PRD body as its requirement.

This implements human-in-the-loop: you refine the PRD through chat, the AI responds with context, and you confirm by converting to tasks.

### Tasks

Tasks are the delivery objects that flow through the pipeline. A task stores:

- **title**, **requirement_markdown**, **acceptance_criteria**, **implementation_steps**
- **current workflow stage** -- position in the pipeline
- **status_group** -- todo, in_progress, waiting_approval, blocked, done
- **assigned_engineer** -- derived from the current stage
- **branch**, **PR**, **deploy URLs** -- execution artifacts
- **comments** -- collaboration thread
- **task_runs** -- execution history
- **tags** -- categorization tags

When a task is created under a project with a workflow, it automatically enters the first stage and inherits that stage's engineer.

### Task Runs

A task run is one concrete execution attempt for a stage. Each AI-executable stage creates a TaskRun record. Task runs track:

| Field | Description |
|-------|-------------|
| workflow stage | Which stage this run belongs to |
| run status | pending -> claimed -> running -> completed/failed/waiting_human |
| engineer | Who executed it |
| attempt_number | How many times this stage has been retried |
| timestamps | claimed_at, started_at, completed_at |
| outcome | Structured result (completed, blocked, failed, needs_human_input) |
| token usage | Tokens consumed and cost (tracked separately) |

### Tags

Tags provide flexible categorization for tasks and PRDs. Tags are scoped to an organization.

Each tag has a **name** and optional **color**. Tags can be assigned to tasks and PRDs, and used as filters on the board.

Common use cases:

- Sprint labels (Sprint 1, Sprint 2, ...)
- Feature groupings (Auth, Payments, Notifications)
- Type classification (Bug, Feature, Tech Debt)
- Priority markers (P0, P1, P2)

**Tag management** happens through the organization detail page at \`/organizations/detail?orgId=X\`. You can create tags with color pickers and delete them.

### Token Spend Tracking

Every AI execution is tracked for cost visibility. The \`token_usages\` table records:

| Field | Description |
|-------|-------------|
| tokens_in | Input tokens consumed |
| tokens_out | Output tokens generated |
| cost_usd | Calculated cost in USD |
| model | Which model was used |
| task_id / task_run_id / prd_id | What entity consumed these tokens |
| user_id | Which user initiated the work |

Token summaries are available per task (\`/tasks/{id}/token-summary\`) and per project (\`/projects/{id}/token-summary\`). This lets you track the monetary cost of AI execution at any granularity.

---

## Stage Lifecycle

### Outcomes

When an AI-executable stage runs, the agent produces one of four outcomes:

| Outcome | Behavior |
|---------|----------|
| \`completed\` | Stage succeeded. Task advances to the next stage. |
| \`needs_human_input\` | Agent needs a decision. Task pauses at \`waiting_approval\`. |
| \`blocked\` | External blocker. Enters rework logic or pauses. |
| \`failed\` | Execution error. Enters rework logic or pauses. |

### Rework Logic

Each stage configures rework behavior:

- **max_rework_attempts** -- how many failures before requiring human input (default: 3)
- **rework_target_stage** -- which stage to fall back to on failure

Example flow with QA Testing (\`max_rework_attempts=2\`, rework_target=Build):

    Build (complete) -> QA (failed, rework #1) -> Build (complete) -> QA (failed, rework #2)
    -> Build (complete) -> QA (failed, rework #3 > max) -> WAITING_HUMAN
    


After the third failure exceeds the max, the task is blocked and requires human intervention.

### Approval Gates

A stage with \`requires_human_approval = true\` pauses the task until a human explicitly approves. The status group shows \`waiting_approval\`.

Non-AI-executable stages (\`is_ai_executable = false\`) with approval enabled act as pure gates -- the task sits there until a human advances it manually or approves the preceding task run.

### Status Groups

Each task has a status_group for quick state identification:

| Group | Meaning |
|-------|---------|
| \`todo\` | Ready for pickup |
| \`in_progress\` | An engineer runtime is actively executing |
| \`waiting_approval\` | Needs human review or decision |
| \`blocked\` | Something is preventing progress |
| \`done\` | All stages completed |

---

## Runtime Architecture

### Container Lifecycle

Each engineer runs inside its own Docker container with Opencode CLI and the DeepSeek model.

**Launch flow:**
1. Backend builds or reuses the runtime Docker image
2. Container is launched on the same Docker network as the backend
3. Container sends engineer-level heartbeat to \`/engineer-runtimes/{id}/heartbeat\`
4. Container polls \`/agent/poll-next-task\` for work in stages assigned to its engineer
5. On claiming a task, sends task-level heartbeats during execution

**Execution flow:**
1. Clone the project repository into \`/tmp/devboss-runtime/task-{id}/repo/\`
2. Create or checkout the task branch
3. Write task bundle files (TASK.md, COMMENTS.md, PROJECT_CONTEXT.md, STAGE_INSTRUCTIONS.md)
4. Invoke \`opencode run --model deepseek/deepseek-v4-pro --dangerously-skip-permissions --format json\`
5. Parse the JSON outcome
6. Push branch changes, create PR if applicable
7. Post a human-readable comment and structured outcome to the backend

### Health Monitoring

Engineer health is tracked via heartbeats:

- **starting** -- container launched, waiting for first heartbeat
- **healthy** -- heartbeats received within the timeout window (90 seconds)
- **heartbeat_missing** -- no heartbeat received within the timeout
- **stopped** -- explicitly stopped by user
- **launch_failed** -- container could not start

### Isolation and Permissions

Runtime containers are Docker-isolated but intentionally given access to:

- Clone and push to GitHub repositories
- Create and switch branches
- Commit code changes
- Run build, test, and deploy commands
- Create pull requests via GitHub API

---

## Authentication and Secrets

### User Authentication

Authentication is handled by an external JWT service. Users sign in with email and password. The JWT token is stored in localStorage and sent with every API request. The AuthGuard component wraps the entire app and redirects unauthenticated users to the login page.

### API Keys

Provider API keys are stored in the Global Configs table and injected into runtime containers:

- \`deepseek_api_key\` -- for Opencode/DeepSeek execution
- \`github_developer_token\` -- for authenticated Git operations and PR creation
- \`aws_access_key_id\` / \`aws_secret_access_key\` / \`aws_region\` -- for AWS deployment

Each key is marked as \`is_secret\` in the config, masking the value in the UI.

---

## Task Bundle

For each claimed task run, the backend assembles a task bundle written to the runtime workspace:

| File | Contents |
|------|----------|
| \`TASK.md\` | Title, status, requirements, acceptance criteria, implementation steps, open questions |
| \`COMMENTS.md\` | Full comment thread with author attribution |
| \`PROJECT_CONTEXT.md\` | Repo URL, branch, deploy config, deployment instructions, engineer skill markdown |
| \`STAGE_INSTRUCTIONS.md\` | Stage-specific instructions from the workflow stage config |
| \`ATTACHMENTS/\` | Uploaded artifact files (logs, screenshots, test reports) |

---

## Stage Instructions

Each workflow stage can have its own **stage instructions** -- free-form markdown that tells the AI exactly what to do. These are stored in the database per stage and included in the task bundle.

Legacy prompt files (\`ai_grooming.md\`, \`in_progress.md\`, etc.) serve as fallbacks when a stage has no custom instructions.

Example for a Build stage:

\`\`\`markdown
You are in the Build stage. Implement the task requirements end-to-end.
- Add or update tests
- Run local verification (tests, lints, builds)
- Commit changes with descriptive messages
- Push the branch to origin
- Do NOT create a pull request

Outcome JSON keys:
- outcome_type: "completed" | "needs_human_input" | "blocked" | "failed"
- summary: what was done
- branch_name: the branch you worked on
\`\`\`

---

## Deployment Configuration

Deployment config is stored on the project as a JSON blob, keeping deployment control inside Dev Boss:

\`\`\`json
{
  "type": "frontend_static_s3",
  "build_command": "npm run build",
  "output_dir": "out",
  "s3_bucket": "my-site-bucket",
  "cloudfront_distribution_id": "E123456789",
  "aws_region": "ap-south-1"
}
\`\`\`

Deployment instructions (free-form text) complement the JSON config with narrative context about deploy order, env variable caveats, and verification steps.

---

## Navigation Map

| Page | Route | Purpose |
|------|-------|---------|
| Overview | \`/\` | Project/engineer/task counts |
| Board | \`/board?projectId=X\` | Kanban board for a project |
| Projects | \`/projects\` | Project CRUD table |
| Workflows | \`/workflows\` | Workflow list |
| Workflow Editor | \`/workflows/edit?workflowId=X\` | Stage configuration |
| PRDs | \`/prds\` | PRD list with org filter |
| PRD Detail | \`/prds/detail?prdId=X\` | Chat, edit, convert to tasks |
| Organizations | \`/organizations\` | Org list |
| Org Detail | \`/organizations/detail?orgId=X\` | Members, tags |
| Engineers | \`/engineers\` | Engineer runtime management |
| Settings | \`/settings\` | Global config store |
| Task Detail | \`/tasks/view?taskId=X\` | Full task view with comments |

All routes use query parameters for dynamic values. The app is a static export with no server-side routing.

---

## Setup Checklist

1. **Global Configs** -- Add \`deepseek_api_key\`, \`github_developer_token\`, AWS credentials
2. **Organization** -- Create an organization (or use the seeded "Dev Boss Workspace")
3. **Engineers** -- Create engineer profiles (backend, frontend, QA, devops)
4. **Workflow** -- Define a workflow with stages and assign engineers to each stage
5. **Tags** -- Create tags under the organization for sprint/feature categorization
6. **Launch runtimes** -- Launch engineer containers from the engineers page
7. **Projects** -- Create projects tagged to the workflow and organization
8. **PRDs** (optional) -- Create PRDs to progressively define requirements, then convert to tasks
9. **Tasks** -- Create tasks under projects; they auto-enter the first stage
10. **Monitor** -- Watch the board; approve gates; review PRs; reply to agent questions

---

## Operating Patterns

### PRD-Driven Development

1. Create a PRD under your organization
2. Chat with the AI to progressively build the document body
3. Review the final markdown
4. Click "Convert to Tasks" and select target projects
5. Tasks are created with the PRD body as requirements

### Direct Task Creation

1. Open the project board
2. Click "Create Task"
3. Fill in requirements, acceptance criteria, and implementation steps
4. The task auto-enters the first workflow stage

### Human Review Gates

1. When a task reaches an approval gate, it shows \`waiting_approval\`
2. Review the AI's output in the task comments
3. Click "Approve" to advance or reply with feedback
4. The task resumes at the next stage

### Cost Tracking

1. Token usage is automatically recorded during AI execution
2. View per-task costs at \`/tasks/view?taskId=X\` (token summary)
3. View per-project costs at the project board (aggregated)
4. Use this data to estimate and budget AI spend

---

## Assumptions

- Single organization per workspace (MVP)
- One repository per project
- One workflow per project
- One AI engineer per workflow stage
- GitHub-hosted source repositories
- Docker available to run engineer containers
- Humans control approvals, PR merges, and deployment triggers
- Opencode CLI with DeepSeek v4 Pro as the AI agent
- Frontend deployed as static files on S3 or any CDN
- External JWT service for authentication

---

## API Reference

The backend exposes a REST API at \`http://backend:8000\`. Full OpenAPI docs are available at \`/docs\`.

### Key Endpoint Groups

| Group | Prefix | Purpose |
|-------|--------|---------|
| Projects | \`/projects\` | Project CRUD, board per project |
| Workflows | \`/workflows\` | Workflow and stage CRUD, reorder |
| Organizations | \`/organizations\` | Org CRUD, member management |
| Engineers | \`/engineers\` | Engineer CRUD, runtime launch/stop/restart |
| Tasks | \`/tasks\` | Task CRUD, comments, retry |
| PRDs | \`/prds\` | PRD CRUD, chat, convert to tasks |
| Tags | \`/tags\`, \`/organizations/{id}/tags\` | Tag CRUD, set tags on tasks/PRDs |
| Tokens | \`/token-usage\`, \`/projects/{id}/token-summary\` | Record and query token spend |
| Agent | \`/agent/\` | Runtime polling, heartbeat, logs, outcomes |
| Board | \`/board\`, \`/projects/{id}/board\` | Kanban lane data |
| Settings | \`/settings\` | Global config key-value store |
`.trim();
