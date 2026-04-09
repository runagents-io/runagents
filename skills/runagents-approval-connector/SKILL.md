---
name: runagents-approval-connector
description: Use when integrating RunAgents approvals with another system or custom interface. Helps preserve approval scope, distinguish approval from consent, and make background resume behavior visible in external workflows.
---

# RunAgents Approval Connector

Use this skill when approvals need to be exposed or controlled outside the default RunAgents console.

## Use this skill for

- custom approval inboxes
- messaging or portal-based approval surfaces
- approval workflow integrations with ticketing or internal ops systems
- exposing scoped approval choices outside the default UI
- making approval decisions and resumed outcomes visible in another product surface

## Workflow

1. Preserve approval semantics.
   The external system must keep these concepts distinct:
   - approval
   - consent
   - approval scope
   - resumed completion after approval

2. Keep scope explicit.
   Support the current scoped approval model:
   - once
   - run
   - agent + user + tool for a time window

3. Design around async behavior.
   Approvals are often decoupled from the original request surface. The connector should make it clear when a run is waiting, approved, resumed, or finished.

4. Validate the entire loop.
   Confirm:
   - the request appears in the external queue
   - the decision is recorded correctly
   - the run resumes
   - the final result reaches the originating surface if needed

5. Keep reviewer language clear.
   The reviewer should always know which user, which agent, which tool, and which scope they are approving.

## Strong defaults

- Fail closed on approval persistence or grant errors.
- Treat approval queue UX as request-centric, not just run-centric.
- Make the resumed result visible, not only the approval decision.

## Example prompt

Use `$runagents-approval-connector` to design an external approval inbox for RunAgents that supports once, run, and timed agent-plus-user-plus-tool approvals.
