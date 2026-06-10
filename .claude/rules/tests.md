---
paths: 
  - /tests/integration.*.py
  - /tests/unit.*.py
---
# Test Writing Standards
- **Naming**: Use descriptive test names formatted as: "should [action] when [condition]"
- **Assertions**: Limit to one primary assertion per test block.
- **Dependencies**: Mock all external API calls; never interact with real endpoints during unit tests.
- **Verification**: Always run `pytest` after modifying a test file and wait for the results.
