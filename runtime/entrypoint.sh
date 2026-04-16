#!/bin/sh
set -eu

python - <<'PY'
from pathlib import Path
import os

from runtime.codex_home import configure_codex_home

configure_codex_home(
    Path("/root/.codex"),
    os.environ.get("DEVBOSS_CODEX_AUTH_JSON"),
    os.environ.get("DEVBOSS_CAVEMAN_ENABLED", "").lower() == "true",
)
PY

exec python -m runtime.main
