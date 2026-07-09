from pathlib import Path

from runtime.executor import run_opencode


def test_run_opencode_extracts_json_from_stdout(tmp_path: Path):
    fake_opencode = tmp_path / "fake-opencode.sh"
    fake_opencode.write_text(
        "#!/bin/sh\n"
        "printf 'log line before\\n'\n"
        "printf '{\"outcome_type\":\"build_complete\",\"summary\":\"done\",\"branch_name\":null,\"pr_url\":null,\"deploy_url\":null,\"blocked_reason\":null}'\n",
        encoding="utf-8",
    )
    fake_opencode.chmod(0o755)

    outcome, raw_output = run_opencode(tmp_path, str(fake_opencode), "deepseek/deepseek-v4-pro", False)

    assert outcome["outcome_type"] == "build_complete"
    assert outcome["summary"] == "done"
    assert raw_output.startswith("log line before")
