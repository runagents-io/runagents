---
name: runagents-observability-triage
description: Use when investigating workspace health, noisy failures, or run trends in RunAgents. Helps move from dashboard symptoms to concrete run evidence, separate operational buckets cleanly, and identify whether the issue is deploy, policy, model, tool, consent, or surface related.
---

# RunAgents Observability Triage

Use this skill when the question is bigger than a single run and you need to understand workspace behavior as an operator.

## Use this skill for

- dashboard triage
- rising failed-run counts
- approval backlog analysis
- consent backlog analysis
- spotting whether an issue is isolated or systemic
- deciding which run or agent to inspect first

## Workflow

1. Start from the workspace view.
   Look at:
   - running runs
   - pending approvals
   - pending consents
   - failed runs
   - affected agents

2. Separate the buckets.
   Treat these as different classes of operational work:
   - deploy and configuration issues
   - approval workload
   - consent workload
   - tool contract failures
   - model or gateway failures
   - surface delivery failures

3. Pick representative runs.
   Use a few concrete runs with event timelines as evidence before making broader claims.

4. Tie symptoms back to the owning layer.
   The goal is to say which subsystem owns the next fix.

5. Produce operator-facing next steps.
   The output should make it easy to decide whether to update a tool, policy, identity provider, model provider, or user-facing surface.

## Strong defaults

- Dashboard counts are triage signals, not conclusions.
- Approval and consent should always be treated separately.
- Prefer concrete run evidence over aggregate guesses.

## Example prompt

Use `$runagents-observability-triage` to analyze this workspace, separate approval backlog from consent backlog, and identify the most likely root cause behind the failed runs.
