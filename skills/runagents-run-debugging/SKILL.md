---
name: runagents-run-debugging
description: Use when a RunAgents run is paused, stuck, or failed. Helps inspect run events, distinguish approval from consent from tool capability errors, and trace whether the user-visible action actually completed.
---

# RunAgents Run Debugging

Use this skill when a deployed agent is not behaving correctly at runtime.

## Use this skill for

- paused runs
- approval-required loops
- consent-required loops
- missing surface responses after resume
- tool capability or scope mismatches
- same-name agent confusion after redeploy

## Workflow

1. Start from the run, not assumptions.
   Collect:
   - run status
   - run events timeline
   - tool request and tool response events
   - linked approval requests if present

2. Classify the stop reason correctly.
   Common categories:
   - `APPROVAL_REQUIRED`
   - `CONSENT_REQUIRED`
   - tool capability denied
   - tool auth token missing or too narrow
   - surface delivery failure after a successful resume

3. Confirm end-to-end success, not only backend success.
   A resumed write can succeed while the user surface still misses the completion message.

4. For agent-specific debugging, prefer the current deployment view.
   Do not mix old runs from a deleted or replaced agent deployment with the current one.

5. If the workflow is multi-surface, check both sides.
   - runtime and governance events
   - user-facing surface output such as web, WhatsApp, or Slack

## Strong defaults

- Always use event timelines for proof.
- Separate approval, consent, capability, and delivery failures.
- Treat “deploy succeeded” and “workflow succeeded” as different checks.

## Example prompt

Use `$runagents-run-debugging` to trace why this Google Workspace assistant run paused, resumed, and still did not show a success message to the user on WhatsApp.
