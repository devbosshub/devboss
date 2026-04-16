# Dev Boss Runtime

Each engineer container runs this polling client. The runtime:

- polls the backend for the next assigned task run
- materializes markdown task context files
- invokes Codex CLI
- posts logs and structured outcomes back to the backend

When `DEVBOSS_CAVEMAN_ENABLED=true`, the runtime also writes a local Codex hook configuration into `/root/.codex` before starting. This enables a terse response style for that engineer without modifying the checked-out repository.

`DEVBOSS_DRY_RUN=true` is the default so the runtime can be exercised safely before a live Codex configuration is attached.
