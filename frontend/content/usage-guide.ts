export const usageGuideMarkdown = `
# Dev Boss Guide

## What Dev Boss Is

Dev Boss is an AI-assisted software delivery workspace. It manages projects, tasks, engineer runtimes, approvals, and execution flow so a human can supervise end-to-end software work without manually coordinating every step.

The system is designed around a simple operating model:

- a human creates a project that points to a Git repository
- a human creates a task under that project
- a human assigns an engineer to the task
- the engineer runtime picks up runnable stages and executes them with Codex inside Docker
- the human reviews, replies, approves, merges, and triggers deployment at the right gates

This is an MVP. It is intentionally opinionated, single-team, and approval-driven.

## Core Modules

### Overview

The overview page is a lightweight landing page. It gives a quick summary of how many projects, engineers, and tasks exist in the workspace.

### Projects

Projects are the main top-level workspace object. Each project stores:

- project name
- repository URL
- default branch
- deployment config as JSON
- deployment instructions as free-form text

Projects are also the place where you open the project board. Each project board shows tasks grouped by workflow stage.

### Engineers

Engineers are reusable AI worker profiles. Each engineer stores:

- engineer name
- template type
- skill markdown
- model name
- runtime image
- tool/runtime settings

An engineer can be launched into its own Docker container. When the container is running, it sends heartbeats to the backend and can poll for work.

### Global Configs

Global Configs store workspace-wide credentials and platform settings. These are shared across projects and runtimes when needed.

Typical examples:

- \`codex_auth_json\`
- \`github_developer_token\`
- \`aws_access_key_id\`
- \`aws_secret_access_key\`
- \`aws_region\`

### Tasks

Tasks are the primary delivery objects. A task stores:

- title
- requirements
- acceptance criteria
- implementation steps
- assigned engineer
- current workflow stage
- branch, PR, deployment metadata
- comments
- task runs
- artifacts

### Task Comments

Comments are the main collaboration thread for each task. Both humans and the runtime use this thread.

Comments support Markdown, so they can be used for:

- clarifications
- status updates
- structured test findings
- deployment notes
- follow-up instructions

### Task Runs

A task run is one concrete execution attempt for a stage such as grooming, build, testing, or deployment. Task runs store:

- execution phase
- run status
- timestamps
- summary
- structured outcome payload

Task runs are useful for understanding what happened and when.

## Runtime Architecture

Each launched engineer runs inside its own Docker container.

The runtime currently works like this:

1. the backend launches an engineer container
2. the container sends a heartbeat to the backend every minute
3. the container polls the backend for the next pending task run
4. once a task is claimed, the runtime creates a clean workspace for that task
5. it clones the project repository into that workspace
6. it prepares the correct branch context for the current stage
7. it writes the task bundle files
8. it invokes Codex CLI
9. it posts readable task comments and a structured outcome back to the backend

The runtime is isolated by Docker, but it is intentionally given enough access to:

- modify repository files
- create branches
- commit changes
- push branches
- call GitHub APIs
- run build and test commands

## Health Ping Flow

Engineer health is tracked with a heartbeat flow:

1. when an engineer is launched, the backend marks it as \`starting\`
2. the runtime sends a heartbeat every minute
3. each heartbeat marks the engineer as \`healthy\`
4. if the backend stops receiving heartbeats within the timeout window, the engineer is marked as \`heartbeat missing\`
5. if the runtime is explicitly stopped, the engineer is marked as \`stopped\`

This tells you whether the container is actually alive and responsive.

## Authentication and Secrets

### Codex

Codex CLI is installed inside the runtime image.

Authentication is currently provided through the \`codex_auth_json\` global config:

- the backend reads \`codex_auth_json\`
- it passes the value into the runtime container
- the runtime writes it to \`/root/.codex/auth.json\`
- Codex CLI then uses that auth state during execution

### GitHub

Git operations and PR creation rely on \`github_developer_token\`.

The runtime uses this token for:

- authenticated repository clone
- branch push
- PR creation through the GitHub API

### AWS

AWS credentials are intended to come from Global Configs and be injected into the runtime when deployment is needed.

## Task Bundle

For each claimed task run, Dev Boss creates a task bundle for Codex. The bundle includes:

- \`TASK.md\`
- \`COMMENTS.md\`
- \`PROJECT_CONTEXT.md\`
- \`STAGE_INSTRUCTIONS.md\`
- attachments when present

This gives Codex the current requirements, history, repo context, deployment context, and stage-specific rules in one place.

## Workflow Stages

### Draft

Human authors the task. This is where the task should become clear, useful, and testable.

Recommended content:

- what needs to be done
- what success looks like
- implementation constraints
- any relevant links or assets

### AI Grooming

AI Grooming is not meant to implement the task.

Its job is to:

- understand the requirement
- inspect the codebase
- identify gaps, assumptions, and risks
- decide whether the task is ready for full implementation

Possible outcomes:

- ask for human clarification
- declare the task ready for build

### Ready for Build

This is a human approval gate. The human confirms that grooming is complete and the task can move into implementation.

### In Progress

This is the implementation stage.

The engineer is expected to:

- work on a task branch
- write code
- run tests or builds where appropriate
- commit and push the branch
- leave the task ready for AI Testing

### AI Testing

This stage validates the implementation. The engineer is expected to:

- continue from the task branch created during implementation
- run validation steps
- compare behavior against acceptance criteria
- produce clear evidence

If AI Testing fails, Dev Boss can automatically loop the task back to \`In Progress\` for rework up to three times. After that, it pauses for human input.

### Human Testing

This is the human validation stage. The human checks:

- user experience
- business correctness
- any final behavior that needs manual confirmation

### Ready to Deploy

This stage is for pull-request readiness, not live deployment.

The engineer is expected to:

- use the task branch
- sync it with the default branch if needed
- resolve safe conflicts
- prepare or create the final PR
- report the PR link back on the task

Human action expected here:

- review the PR
- merge the PR into the project's default branch

### Deployment

This stage represents actual deployment work after the PR has been merged.

The engineer is expected to:

- work from the project's default branch
- use the project's deployment config
- use the project's deployment instructions
- run build and deployment steps
- attach deployment evidence

Once deployment succeeds, the task moves to \`Archived\`.

### Archived

Archived means the delivery flow is finished and the task is no longer active on the board.

## Stage Instruction Files

Dev Boss uses global markdown instruction files for stage behavior. These live in the backend prompt folder and are included in the task bundle as \`STAGE_INSTRUCTIONS.md\`.

Current stage prompt files:

- \`ai_grooming.md\`
- \`in_progress.md\`
- \`ai_testing.md\`
- \`ready_to_deploy.md\`
- \`deployment.md\`

These files define what Codex should do, what it must not do, and how it should choose outcomes.

## Project Deployment Configuration

Deployment configuration is stored on the project itself, not inside the repository.

This keeps deployment control inside Dev Boss and allows different projects to use different deployment models.

The deploy config is entered as JSON so it stays flexible.

Example:

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

## Project Deployment Instructions

Projects can also store deployment instructions alongside the deploy config.

This is useful when the project needs extra context beyond structured JSON, for example:

- exact deployment order
- caveats about environment variables
- how to verify success
- special cleanup or invalidation steps

Example:

- build using \`npm run build\`
- upload the contents of \`out/\` to the configured S3 bucket
- invalidate CloudFront after upload
- verify the homepage responds successfully

## Current Deployment Assumption

The intended deployment flow is:

1. implementation happens on a task branch
2. AI Testing validates that branch
3. Ready to Deploy prepares the final PR
4. the human merges the PR
5. Deployment runs from the project's default branch
6. the task is archived after successful deployment

## What Works Today

Current implemented capabilities include:

- project management
- engineer management
- global config management
- project board with workflow lanes
- engineer container launch, stop, and restart
- engineer heartbeat monitoring
- task creation, editing, deletion, retry
- markdown task comments
- task-run tracking
- repo checkout in runtime
- branch creation and push
- PR creation flow for release handoff
- stage-specific task bundles for Codex

## What Is Still Evolving

Areas that are still MVP-level or partially implemented:

- deployment is still prompt-driven rather than fully adapter-driven
- multi-agent collaboration per task is not implemented
- production-grade secret management is not implemented
- there is no advanced RBAC or multi-tenant support
- deployment evidence storage is still basic
- cost controls and scheduling policies are minimal

## Assumptions

Dev Boss currently assumes:

- one internal team
- one repository per project
- one assigned engineer per task at a time
- GitHub-hosted source repositories
- Docker available to run engineer containers
- humans still control key approvals and merges
- deployment credentials are centrally managed in Global Configs

## Suggested Setup Checklist

When bringing up a new workspace, do this in order:

1. add required Global Configs
2. create at least one engineer profile
3. launch the engineer
4. create a project with repo URL and default branch
5. add deployment config and deployment instructions if deployment is needed
6. create a task and assign the engineer
7. move the task into the first runnable stage
8. monitor the task thread and approve handoffs as needed

## Recommended Global Configs

For a typical GitHub + Codex + AWS workflow, these are the main configs to add:

- \`codex_auth_json\`
- \`github_developer_token\`
- \`aws_access_key_id\`
- \`aws_secret_access_key\`
- \`aws_region\`

## How Humans Should Use Dev Boss

The cleanest operating pattern is:

- write tasks clearly
- treat AI Grooming as a readiness review, not implementation
- use task comments for clarifications and approvals
- review the PR in Ready to Deploy
- merge manually
- then trigger Deployment

This keeps Dev Boss aligned with an auditable, approval-driven SDLC while still letting the AI runtime do most of the heavy lifting.
`.trim();
