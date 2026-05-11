---
title: Audit Logs
description: How RunAgents records run events, approval decisions, and identity context so teams can inspect governed actions after the fact.
---

# Audit logs

RunAgents records audit history at the run level.

That means operators can inspect what happened during execution without losing the link between the original request, the policy outcome, the approval decision, and the final system action.

## What is captured

Current docs describe audit history across:

- run events and state transitions
- blocked actions and payload hashes
- approval grants and rejections
- identity propagation context
- risk tags and tool metadata that surface in dashboards and logs

## Where to inspect audit history

- [Run lifecycle](../operations/runs.md)
- [Runs API](../api/runs.md)
- [Approvals](../platform/approvals.md)
- [Identity providers](../platform/identity-providers.md)
- [Registering tools](../platform/registering-tools.md)

## Why it matters

The audit surface is useful because it stays attached to the run itself. Teams do not need to reconstruct approval state, policy decisions, and action outcomes from disconnected systems to understand what happened.
