#!/usr/bin/env python3
"""filter_test_output.py - a Claude Code PreToolUse hook that keeps test output short.

When Claude is about to run a plain test command (npm test, pytest, go test ...),
this rewrites it to keep only the LAST N lines of output (default 100), and it keeps
the real exit code, so a failing test still looks like a failure.

How Claude Code calls a hook: it sends JSON on standard input and reads JSON from standard output.
Anything that is not a simple test command is left alone (we print {}).

Install: see templates/claude-settings.cost.example.json and guide/02.
Change the line count with the environment variable TBT_TAIL_LINES.
Python 3.8+, standard library only.
"""
import json
import os
import re
import sys

# Only plain commands. No pipes, no &&, no quotes, no redirects, no $( ).
SIMPLE = re.compile(
    r"^(npm test|npm run test|pnpm test|pnpm run test|yarn test|pytest|python -m pytest|python3 -m pytest|go test|cargo test)"
    r"( [A-Za-z0-9_./=:,@%+\-]*)*$"
)


def wrap(cmd, lines):
    # pipefail keeps the test command's exit code even though tail is last in the pipe
    return f"set -o pipefail; {cmd} 2>&1 | tail -n {int(lines)}"


def decide(event, lines=100):
    if event.get("tool_name") != "Bash":
        return {}
    tool_input = event.get("tool_input") or {}
    cmd = str(tool_input.get("command") or "").strip()
    if not cmd or "|" in cmd or "tail -n" in cmd or not SIMPLE.match(cmd):
        return {}
    new_input = dict(tool_input)
    new_input["command"] = wrap(cmd, lines)
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": new_input}}


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        print("{}")
        return 0
    try:
        lines = int(os.environ.get("TBT_TAIL_LINES", "100"))
    except ValueError:
        lines = 100
    print(json.dumps(decide(event, max(10, min(lines, 2000)))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
