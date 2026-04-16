import json
import subprocess
import sys
from pathlib import Path

from runtime.codex_home import configure_codex_home


def test_configure_codex_home_writes_auth_and_caveman_files(tmp_path: Path):
    home_dir = tmp_path / ".codex"

    configure_codex_home(home_dir, '{"provider":"chatgpt"}', True)

    assert (home_dir / "auth.json").read_text(encoding="utf-8") == '{"provider":"chatgpt"}'
    assert (home_dir / "config.toml").read_text(encoding="utf-8") == "[features]\ncodex_hooks = true\n"

    hooks_payload = json.loads((home_dir / "hooks.json").read_text(encoding="utf-8"))
    session_start_hook = hooks_payload["hooks"]["SessionStart"][0]["hooks"][0]
    assert session_start_hook["type"] == "command"
    assert session_start_hook["command"] == "python3 /app/runtime/caveman_session_start.py"


def test_configure_codex_home_removes_caveman_files_when_disabled(tmp_path: Path):
    home_dir = tmp_path / ".codex"
    configure_codex_home(home_dir, None, True)

    configure_codex_home(home_dir, None, False)

    assert not (home_dir / "config.toml").exists()
    assert not (home_dir / "hooks.json").exists()


def test_caveman_session_start_emits_structured_context():
    result = subprocess.run(
        [sys.executable, "-m", "runtime.caveman_session_start"],
        input='{"source":"startup"}',
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "terse" in payload["hookSpecificOutput"]["additionalContext"].lower()
