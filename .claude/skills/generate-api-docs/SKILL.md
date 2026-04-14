---
name: generate-api-docs
description: Generate markdown API documentation for a router module. Use when documenting endpoints, request/response schemas, auth requirements, and error responses.
disable-model-invocation: true
---

# /generate-api-docs

Generate markdown API documentation for a router module.

## Instructions

1. Read the specified router file
2. For each endpoint, document:
   - Method + path
   - Auth required (yes/no, role)
   - Request body schema (field, type, required, constraints)
   - Response schema
   - Error responses (status code + condition)
   - Known defects or TODOs (from inline comments)
3. Output a single clean markdown document

## Output Format

# {Module Name} API

## `METHOD /path`
**Auth**: Bearer token required / None
**Request**: ...
**Response `2xx`**: ...
**Errors**: ...
