---
title: Core Concepts
description: The key mental models behind RunAgents, including identity propagation, policy enforcement, approvals, consent, and run-level auditability.
---

# Core concepts

RunAgents is built around one core idea: agent actions should be governed before they reach real systems.

The docs below are the fastest way to understand that model end to end.

## The mental model

Every governed agent action passes through the same control path:

1. **Identity is attached at ingress** so the platform knows who initiated the request.
2. **Policy is evaluated at runtime** for the specific tool, method, and path.
3. **Approval can pause the action** when the policy decision requires a reviewer.
4. **Credentials are injected at egress** only after the action is allowed to proceed.
5. **Run history and audit events stay attached** to the same execution record.

## Read these first

- [Architecture](../concepts/architecture.md) explains the three-stage ingress, runtime, and egress flow.
- [Identity propagation](../concepts/identity-propagation.md) shows how user identity moves from client to agent to tool.
- [Policy model](../concepts/policy-model.md) explains how `allow`, `deny`, and `approval_required` decisions are evaluated.
- [OAuth & consent](../concepts/oauth-consent.md) covers user consent flows and token handling for OAuth tools.
- [Run lifecycle](../operations/runs.md) shows how the platform records state transitions, approvals, and outcomes on the same run timeline.

## Why these concepts matter together

RunAgents does not treat identity, policy, approvals, and credentials as separate integrations. They are part of the same execution path. That is what makes the platform useful once agents stop drafting and start changing real systems.

## Next steps

| Goal | Read next |
| --- | --- |
| Build your first governed agent | [Quickstart](quickstart.md) |
| Bring an existing agent into RunAgents | [Writing agents](writing-agents.md) |
| Understand how risky actions are paused | [Approvals](../platform/approvals.md) |
| See how actions are tracked in production | [Run lifecycle](../operations/runs.md) |
