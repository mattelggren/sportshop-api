#!/bin/bash
# Post-write hook: run bandit security scan on modified Python files
# Claude Code triggers this after writing any .py file

FILE="$1"

if [[ "$FILE" == *.py ]]; then
    echo "=== Security scan: $FILE ==="
    bandit -c pyproject.toml "$FILE" --severity-level medium
fi
