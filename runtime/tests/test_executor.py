from pathlib import Path

from runtime.executor import run_codex


def test_run_codex_extracts_json_from_stdout(tmp_path: Path):
    fake_codex = tmp_path / "fake-codex.sh"
    fake_codex.write_text(
        "#!/bin/sh\n"
        "printf 'log line before\\n'\n"
        "printf '{\"outcome_type\":\"build_complete\",\"summary\":\"done\",\"branch_name\":null,\"pr_url\":null,\"deploy_url\":null,\"blocked_reason\":null}'\n",
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)

    outcome, raw_output = run_codex(tmp_path, str(fake_codex), False)

    assert outcome["outcome_type"] == "build_complete"
    assert outcome["summary"] == "done"
    assert raw_output.startswith("log line before")
