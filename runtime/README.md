# Dev Boss Runtime

Each engineer container runs this polling client. The runtime:

- polls the backend for the next assigned task run
- materializes markdown task context files
- invokes Opencode CLI
- posts logs and structured outcomes back to the backend

The runtime uses `opencode run` with `--dangerously-skip-permissions` and `--format json` for non-interactive execution. The model is selected via the engineer's `model_provider` and `model_name` settings, passed as `--model <provider>/<model>`.

`DEVBOSS_DRY_RUN=true` is the default so the runtime can be exercised safely before live API keys are configured.
