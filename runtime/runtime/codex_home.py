from __future__ import annotations

import json
from pathlib import Path


HOOK_SCRIPT_PATH = "/app/runtime/caveman_session_start.py"
CONFIG_FILE_NAME = "config.toml"
HOOKS_FILE_NAME = "hooks.json"
AUTH_FILE_NAME = "auth.json"


def _config_toml() -> str:
    return "[features]\ncodex_hooks = true\n"


def _hooks_json() -> str:
    payload = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python3 {HOOK_SCRIPT_PATH}",
                            "statusMessage": "Caveman terse mode enabled",
                        }
                    ],
                }
            ]
        }
    }
    return json.dumps(payload, indent=2) + "\n"


def configure_codex_home(home_dir: Path, auth_json: str | None, caveman_enabled: bool) -> None:
    home_dir.mkdir(parents=True, exist_ok=True)

    if auth_json:
        auth_path = home_dir / AUTH_FILE_NAME
        auth_path.write_text(auth_json, encoding="utf-8")
        auth_path.chmod(0o600)

    config_path = home_dir / CONFIG_FILE_NAME
    hooks_path = home_dir / HOOKS_FILE_NAME
    if caveman_enabled:
        config_path.write_text(_config_toml(), encoding="utf-8")
        hooks_path.write_text(_hooks_json(), encoding="utf-8")
    else:
        config_path.unlink(missing_ok=True)
        hooks_path.unlink(missing_ok=True)
