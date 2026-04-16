from __future__ import annotations

import json
import sys


CAVEMAN_CONTEXT = (
    "Use a terse, high-signal style. "
    "Skip filler, preambles, and repetition. "
    "Keep wording minimal while preserving correctness, concrete details, and safety. "
    "Use bullets only when they improve scanability."
)


def main() -> int:
    # Codex sends hook payload on stdin. We do not need to inspect it for this fixed context,
    # but we consume it so the process behaves predictably if the payload grows over time.
    _ = sys.stdin.read()
    sys.stdout.write(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": CAVEMAN_CONTEXT,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
