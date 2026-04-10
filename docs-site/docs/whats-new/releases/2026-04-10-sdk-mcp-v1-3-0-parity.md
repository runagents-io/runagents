# SDK & MCP v1.3.0: Catalog, Governance, Identity, and Run Operations

RunAgents `v1.3.0` brings the public Python SDK and MCP server much closer to the management surface already available in the CLI.

This release matters if you use:

- Python automation against RunAgents APIs
- Claude Code, Cursor, Codex, or similar assistants through `runagents-mcp`
- the public SDK as the foundation for internal deployment and operations workflows

## Highlights

- **Catalog parity** — assistants and Python automation can now list catalog agents, inspect manifests, list versions, and deploy directly from catalog blueprints.
- **Governance parity** — policies and approval connectors are now first-class SDK and MCP resources instead of CLI-only workflows.
- **Identity parity** — identity providers can now be listed, inspected, created, updated, and deleted from Python and MCP.
- **Run operations parity** — the SDK and MCP server now support richer run inspection, including `get`, event filtering, timelines, waiting for terminal state, and full run export.
- **Deploy and approval parity** — deploy flows now accept policies, identity providers, drafts, artifacts, and framework hints; approvals now expose scoped approval parameters.

## What shipped

### Python SDK

The Python client now exposes:

- `client.catalog`
- `client.policies`
- `client.approval_connectors`
- `client.identity_providers`

It also expands:

- `client.runs`
  - `list`
  - `get`
  - `events`
  - `timeline`
  - `wait`
  - `export`
- `client.agents.deploy(...)`
  - source deploy options
  - draft and artifact deploy paths
  - policy binding
  - identity-provider binding
- `client.approvals.approve(...)`
  - `scope`
  - `duration`

### MCP server

The MCP server now supports assistant-facing tools for:

- catalog discovery and deploy
- policy read/apply/delete/translate
- approval connector configuration, defaults, testing, and activity
- identity provider management
- richer run debugging and export
- scoped approval decisions

## Why this release exists

Before `v1.3.0`, the CLI had moved ahead of the public Python SDK and MCP story.

That meant the public repo could truthfully say RunAgents supported:

- catalog deployment
- policy workflows
- approval connectors
- identity providers
- richer run operations

but not all of those were available consistently from:

- the Python SDK
- the MCP server used by coding assistants

`v1.3.0` closes much of that gap and makes the public SDK/MCP surface feel more like a mature product ecosystem rather than a narrow helper package.

## Release guidance

Move to `v1.3.0` if you want:

- assistant workflows that can inspect and manage more of the real platform
- Python automation for catalog, governance, identity, and operations
- a more consistent public story across CLI, SDK, MCP, docs, and releases

## Notes

- The MCP command still ships through `pip install runagents[mcp]`.
- This release does **not** introduce a separately published `runagents-mcp` package.
- The CLI release channels remain unchanged:
  - GitHub releases
  - npm
  - Homebrew
  - S3 install script
- The Python SDK and MCP surface ship through the unified versioned Python package on PyPI.
