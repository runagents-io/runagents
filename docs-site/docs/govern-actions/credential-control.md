---
title: Credential Control
description: How RunAgents stores, scopes, and injects credentials only after policy allows an agent action to proceed.
---

# Credential control

RunAgents keeps credentials out of agent code and injects them only when an outbound action is allowed to proceed.

## The control model

Credential handling follows the same action path as identity, policy, and approvals:

1. The incoming request is associated with a user or service identity.
2. Policy is evaluated for the requested tool call.
3. If approval is required, the run pauses before the action executes.
4. Only after the decision is allowed does RunAgents inject the tool or provider credential.

## What this protects

This model helps teams avoid:

- hardcoded API keys in agent code
- long-lived credentials embedded in prompts or repositories
- shared bot credentials with no action-level context
- unreviewed access to high-risk external systems

## Where credential control shows up

- [Registering tools](../platform/registering-tools.md) covers API key, OAuth2, and capability configuration.
- [OAuth & consent](../concepts/oauth-consent.md) explains user-consent and refresh-token handling.
- [Model providers](../platform/model-providers.md) shows how provider credentials are stored and injected by the gateway.
- [Tools API](../api/tools.md) documents the tool credential fields and secure storage behavior.

## Related concepts

- [Identity propagation](../concepts/identity-propagation.md)
- [Policy model](../concepts/policy-model.md)
- [Approvals](../platform/approvals.md)
