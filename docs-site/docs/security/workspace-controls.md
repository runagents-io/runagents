---
title: Workspace Controls
description: How RunAgents scopes configuration, credentials, identities, and runtime operations within a workspace boundary.
---

# Workspace controls

A RunAgents workspace is the operational boundary for agents, tools, identities, runs, and approvals.

## Workspace-scoped controls

Current docs show workspace scoping in several places:

- CLI and SDK configuration target a specific workspace endpoint and namespace.
- Agents, tools, model providers, and approvals are managed within that workspace.
- Identity providers are configured for the workspace so incoming requests can be validated and attributed.
- Run history and approval state stay attached to the workspace that executed them.

## What teams usually control per workspace

- platform endpoint and API key
- namespace used for API scoping
- identity providers
- registered tools and model providers
- deployed agents and drafts
- runtime approvals and audit history

## Read the related docs

- [CLI installation and configuration](../cli/installation.md)
- [Python SDK](../sdk/index.md)
- [Identity providers](../platform/identity-providers.md)
- [Dashboard](../platform/dashboard.md)
- [Billing and pricing](../api/billing.md)
