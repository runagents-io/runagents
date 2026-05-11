---
title: Security Overview
description: The security model behind RunAgents, including identity propagation, policy enforcement, approvals, credential isolation, and run-level auditability.
---

# Security overview

RunAgents is designed so agent actions are governed before they reach production systems.

## The security model

Every governed action follows the same control path:

- **Identity propagation** ties the request to a real user or service identity.
- **Policy enforcement** evaluates the specific tool call before it executes.
- **Approvals** pause high-risk writes until a reviewer decides.
- **Credential isolation** keeps API keys and tokens out of agent code.
- **Run-level auditability** records the state transitions, approvals, and outcomes together.

## Read the underlying docs

- [Architecture](../concepts/architecture.md)
- [Identity propagation](../concepts/identity-propagation.md)
- [Policy model](../concepts/policy-model.md)
- [Approvals](../platform/approvals.md)
- [Self-hosted deployment](../self-hosted/deployment.md)

## Security by default

RunAgents does not assume that deployment, identity, approvals, and observability are separate concerns. The platform treats them as part of the same execution path so teams can safely move agents from sandboxed assistants to real system operators.
