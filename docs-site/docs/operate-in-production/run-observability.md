---
title: Run Observability
description: Inspect run timelines, approvals, blocked actions, and outcomes without reconstructing agent behavior from disconnected logs.
---

# Run observability

RunAgents treats the run as the operational unit for debugging and governance.

Instead of piecing events together from multiple systems, operators can follow a single run record from request to outcome.

## What operators can inspect

A governed run can include:

- execution status and timestamps
- LLM and tool-call events
- approval-required pauses
- approval grants or rejections
- blocked actions and payload hashes
- model budget failures and other runtime errors

## Where to inspect it

- [Dashboard](../platform/dashboard.md) for active runs, pending approvals, and recent operator work
- [Run lifecycle](../operations/runs.md) for the state machine and event model
- [Runs API](../api/runs.md) for programmatic inspection and export

## Why this matters

Observability is more useful when it stays attached to the action path.

That means the same operational surface can answer:

- who triggered the run
- which agent and tool were involved
- whether policy allowed or paused the action
- who approved it, if approval was required
- what outcome completed or failed the run
