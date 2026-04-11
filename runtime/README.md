# Dev Boss Runtime

Each engineer container runs this polling client. The runtime:

- polls the backend for the next assigned task run
- materializes markdown task context files
- invokes Codex CLI
- posts logs and structured outcomes back to the backend

`DEVBOSS_DRY_RUN=true` is the default so the runtime can be exercised safely before a live Codex configuration is attached.

