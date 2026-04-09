---
name: runagents-approval-policy
description: Use when designing or troubleshooting RunAgents approval-required policy. Helps separate approval from consent, tie policy to specific tools, and choose the right approval scope: once, this run, or this agent plus this user plus this tool for a time window.
---

# RunAgents Approval Policy

Use this skill when a RunAgents workflow needs governed writes or when approvals are behaving unexpectedly.

## Use this skill for

- creating approval-required rules for write actions
- choosing the right approval scope
- debugging repeated approval loops
- explaining approval vs consent to operators
- validating that runtime grants align with policy intent

## Approval model to use

All reusable approvals should stay tied to a specific tool.

Use these scopes:

- `once` — approve one exact blocked action
- `run` — approve matching actions for the current run
- `agent_user_ttl` — approve matching actions for this agent, this user, and this tool for a limited time window

## Workflow

1. Separate the concepts first.
   - approval = another human decision is required
   - consent = the end user must authorize the tool

2. Scope policy to the tool.
   Approval should not become a broad agent-wide bypass.

3. Choose the smallest scope that matches the user need.
   - use `once` for single sensitive writes
   - use `run` for retries and resumed actions inside one workflow
   - use `agent_user_ttl` when the same user will repeat the same tool action during a short window

4. Check the three layers together.
   - static policy says the write is approval-required
   - approval grant provides temporary authorization after approval
   - runtime matches the grant before falling back to `approval_required`

5. When troubleshooting, fail closed.
   If grant persistence or consume semantics fail, do not treat the action as approved.

## Strong defaults

- Reads should usually be allow-listed explicitly.
- Writes should usually be approval-required unless there is a strong reason otherwise.
- Approval and consent should be distinct in UI, docs, and operator language.
- For customer-facing explanations, say what will happen after approval: the run resumes automatically.

## Example prompt

Use `$runagents-approval-policy` to design a policy for a Google Workspace assistant where reads are allowed, writes require approval, and reviewers can choose once, this run, or one hour for the same user and tool.
