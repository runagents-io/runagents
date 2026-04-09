---
name: runagents-observability-connector
description: Use when exporting RunAgents runs, events, or operational signals into another observability system. Helps keep approval, consent, runtime, and delivery signals distinct so external dashboards and alerts stay actionable.
---

# RunAgents Observability Connector

Use this skill when RunAgents operational data needs to flow into another observability, analytics, or compliance system.

## Use this skill for

- exporting runs and events to external observability tools
- designing alerts around paused, failed, or resumed workflows
- feeding RunAgents activity into SIEM, data warehouse, or internal dashboards
- keeping approval and consent signals distinct in downstream analytics
- building dashboards that tie workspace symptoms back to concrete runs

## Workflow

1. Start from the external use case.
   Decide whether the destination system is for:
   - operator dashboards
   - alerting
   - compliance logging
   - business analytics

2. Keep event semantics intact.
   Do not collapse these into one generic “pause” bucket:
   - approval-required
   - consent-required
   - failed
   - resumed
   - completed

3. Preserve linkage.
   Make it possible to move from aggregate symptoms to the underlying run and event evidence.

4. Align alert thresholds with operational meaning.
   Approval backlog, consent backlog, and failed runs should not all page the same way.

5. Validate with a real incident shape.
   Test the connector against one approval-blocked run, one consent-blocked run, and one true failure.

## Strong defaults

- External dashboards should help operators decide what subsystem owns the next fix.
- Keep approval and consent as separate downstream signals.
- Favor event-rich exports over shallow counters when building operational tooling.

## Example prompt

Use `$runagents-observability-connector` to design a connector that sends RunAgents run and event data to an external observability stack without losing approval, consent, or resume semantics.
