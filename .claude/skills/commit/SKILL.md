---
name: commit
description: Create a git commit
disable-model-invocation: true
allowed-tools: Bash(git *)
---

## Context
  - Branch: !`git branch --show-current`
  - Status: !`git status --short`
  - Diff: !`git diff HEAD`
  - Recent commits: !`git log --oneline -5`

## Task
Based on the above, write a conventional commit message and commit.
