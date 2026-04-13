#!/bin/bash
# Pre-commit hook: lint + test gate
# Claude Code triggers this before committing any file changes

set -e

echo "=== SportShop pre-commit: ruff ==="
ruff check app/ tests/

echo "=== SportShop pre-commit: pytest (unit only) ==="
pytest tests/unit/ -q --tb=short

echo "=== Pre-commit passed ==="
