# OpenAPI Contract

Use this page when you want the canonical, machine-readable definition of the public RunAgents REST API.

!!! info "Reference Views"
    [:material-book-open-variant: Redoc Reference](redoc.md){ .md-button .md-button--primary }
    [:material-api: Swagger UI](swagger.md){ .md-button }

    Use Redoc or Swagger UI for interactive exploration. Use the OpenAPI contract when you want the underlying source of truth for generated docs, validation, or client tooling.

## Source of Truth

The contract lives at:

```text
openapi/openapi.yaml
```

This file is the machine-readable source for:

- Swagger UI
- Redoc
- client generation
- API validation in CI

## Current Coverage

The current OpenAPI contract covers:

- approvals
- runs
- catalog
- deploy
- policies
- approval connectors
- identity providers
- agents
- tools
- model providers
- builds
- billing
- ingestion

These groups were prioritized because they are already documented publicly and map directly to the public CLI, SDK, and MCP workflows.

## How to Use It

- Treat the OpenAPI file as the canonical REST contract where coverage exists.
- Download the published docs copy from [`/api/openapi.yaml`](openapi.yaml).
- Use the curated Markdown guides in this section for examples and workflow explanations.
- Use [Redoc Reference](redoc.md) or [Swagger UI](swagger.md) when you want an interactive view of the same contract.
