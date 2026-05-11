---
title: Data Handling
description: The main categories of data RunAgents processes and how the platform keeps credentials and sensitive execution context out of agent code.
---

# Data handling

RunAgents processes the data required to deploy agents, govern their actions, and operate them in production.

## Data categories

The platform may handle:

- agent source files during analysis and deployment
- tool and model-provider configuration metadata
- stored tool, OAuth, and provider credentials
- run history, events, and approval records
- user identity claims used for propagation and auditability
- build artifacts and deployment metadata

## Handling model and tool credentials

Credentials are managed by the platform and injected at the network or gateway layer. Agent code does not need to embed provider keys, OAuth secrets, or downstream API credentials.

The current docs covering that behavior are:

- [Registering tools](../platform/registering-tools.md)
- [Model providers](../platform/model-providers.md)
- [Credential control](../govern-actions/credential-control.md)

## Source analysis and secrets

When source code is analyzed for deployment, RunAgents can detect likely hardcoded secrets and flag them. The ingestion flow is designed so detected secret values are not stored or logged as part of the analysis output.

See [Ingestion API](../api/ingestion.md) for the current analyzer behavior.

## Related security docs

- [Security overview](security-overview.md)
- [Audit logs](audit-logs.md)
- [Self-hosted deployment](../self-hosted/deployment.md)
