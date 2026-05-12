# What's New

This section highlights the most important product updates across the RunAgents platform.

Use it to:

- see what changed recently
- understand why a release matters
- find upgrade notes before rolling changes into production
- jump from release storytelling into the deeper reference docs

## Latest releases

### May 12, 2026

[RunAgents v1.4.1: CLI Install Path Fixes](releases/2026-05-12-v1-4-1-cli-install-path-fixes.md)

Highlights:

- npm installs now restore the expected `runagents` entrypoint
- the Python wrapper now downloads and launches the native CLI correctly on first run
- this patch release keeps npm, PyPI, CLI binaries, Homebrew, docs, and S3 aligned after `v1.4.0`

### May 12, 2026

[RunAgents v1.4.0: Model Budgets, Safer Edits, and Smoother Operations](releases/2026-05-12-v1-4-0-model-budgets-safer-edits-and-smoother-operations.md)

Highlights:

- model budgets and spend visibility for production workspaces
- safer edit flows across agents, tools, policies, model providers, and identity providers
- faster inventory and deployment operations in the console
- smoother runtime and operator workflow continuity

### April 10, 2026

[RunAgents v1.3.1: Release Pipeline Hardening](releases/2026-04-10-v1-3-1-release-pipeline-hardening.md)

Highlights:

- PyPI Trusted Publishing is now wired into the GitHub release workflow
- the public release pipeline is aligned across CLI, SDK, MCP, docs, npm, Homebrew, and S3
- this patch release hardens the delivery path for the SDK/MCP work introduced in `v1.3.0`

### April 10, 2026

[SDK & MCP v1.3.0: Catalog, Governance, Identity, and Run Operations](releases/2026-04-10-sdk-mcp-v1-3-0-parity.md)

Highlights:

- catalog, policies, approval connectors, identity providers, and richer runs now land on the public SDK and MCP surface
- deploy and approval flows now expose more of the production governance model from Python and assistant tools
- the unified release line now feels much more consistent across CLI, SDK, MCP, docs, and PyPI

### April 9, 2026

[CLI v1.2.0: Governance and Operations from the Terminal](releases/2026-04-09-cli-v1-2-0-governance-and-operations.md)

Highlights:

- catalog deployment, policy management, identity providers, and approval connectors from the CLI
- richer run debugging and export workflows
- stronger deploy ergonomics and better assistant context export

### April 9, 2026

[Scoped Approvals, Clearer Operations, and Better Messaging Workflows](releases/2026-04-09-scoped-approvals-console-messaging.md)

Highlights:

- scoped approvals for governed writes
- clearer approval versus consent handling in the console
- Google Workspace calendar writes under policy control
- stronger pause-and-resume behavior for messaging workflows

## How to use this section

- Start here if you want a quick overview of recent platform changes.
- Use the release notes to understand impact and rollout considerations.
- Use the API, CLI, SDK, and platform reference docs for implementation details.
