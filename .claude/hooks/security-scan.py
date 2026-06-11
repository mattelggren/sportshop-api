#!/usr/bin/env python3
import json
import subprocess
import sys

data = json.load(sys.stdin)

if data.get("tool_name") != "Write":
    sys.exit(0)

file_path = data.get("tool_input", {}).get("file_path", "")
if not file_path.endswith(".py"):
    sys.exit(0)

result = subprocess.run(
    ["bandit", "-c", "pyproject.toml", file_path, "--severity-level", "medium"],
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"Bandit findings in {file_path}:\n{result.stdout}"
        }
    }))

sys.exit(0)
