---
name: runagents-action-plan-workflow
description: Use when driving RunAgents through context export, action plans, validate, and apply. Helps external assistants generate deterministic changes safely and keeps plan-based workflows audit-friendly.
---

# RunAgents Action Plan Workflow

Use this skill when working with RunAgents through exported context and action plans instead of ad hoc imperative commands.

## Use this skill for

- Codex / Claude Code / Cursor deployment loops
- exporting workspace context for assistant reasoning
- generating deterministic `plan.json` changes
- validating before applying
- keeping assistant-driven infrastructure changes auditable

## Workflow

1. Export current context first.
   Use the latest workspace snapshot before asking an assistant to propose changes.

2. Treat the plan as the contract.
   The assistant should produce explicit actions, not vague prose.

3. Validate before apply every time.
   Use validation as a hard gate, especially for production changes.

4. Keep intent idempotent.
   Stable action identifiers and stable sequencing matter for retries and repeat runs.

5. Re-export context after apply.
   Confirm that the workspace now matches the intended state.

## Strong defaults

- Prefer action plans for assistant-driven production changes.
- Keep `continue_on_error: false` for important sequences.
- Store plans in version control or another audit surface.
- Pair this skill with `runagents-tool-onboarding`, `runagents-approval-policy`, or `runagents-catalog-deploy` when the task includes those domains.

## Example prompt

Use `$runagents-action-plan-workflow` to turn this requested RunAgents change into a deterministic plan, tell me how to validate it, and call out anything risky before apply.
