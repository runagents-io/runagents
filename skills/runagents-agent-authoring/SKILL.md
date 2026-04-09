---
name: runagents-agent-authoring
description: Use when writing or refactoring a RunAgents agent. Helps choose the right authoring style, keep agent logic focused on reasoning instead of security plumbing, and validate that tool, model, and runtime assumptions match the deployed platform.
---

# RunAgents Agent Authoring

Use this skill when creating or updating an agent that will run on RunAgents.

## Use this skill for

- writing a new `agent.py`
- refactoring an agent from local-only logic to platform-aware runtime usage
- choosing between SDK-first and framework-based agent patterns
- making tool calls and chat calls fit the RunAgents runtime model
- keeping agent code clean when identity, policy, and auth are handled by the platform

## Workflow

1. Start with the job to be done.
   Define:
   - what the agent decides
   - what tools it needs
   - what user identity or approvals matter
   - what interface sits in front of it

2. Keep the agent focused on logic.
   The platform should own:
   - tool auth
   - identity propagation
   - approval and consent orchestration
   - outbound access control

3. Choose the simplest authoring model that fits.
   - use the RunAgents SDK by default
   - use framework integrations only when the project already depends on them or the workflow complexity justifies it

4. Design tool usage around the registered tool contract.
   Do not assume the agent can call arbitrary endpoints. Match your code to the tool capabilities and auth mode that actually exist in the workspace.

5. Validate with a real run after code changes.
   Check:
   - tool calls succeed
   - model responses route correctly through the gateway
   - approvals or consent occur where expected
   - the user-facing outcome matches the task intent

## Strong defaults

- Prefer readable orchestration over giant prompts.
- Let RunAgents handle security plumbing.
- Treat the Google Workspace assistant as a reference shape for multi-tool, policy-aware agents.
- If the workflow is user-facing, design for pause and resume from the start.

## Example prompt

Use `$runagents-agent-authoring` to refactor this agent so it follows RunAgents SDK patterns, relies on platform tool auth, and is ready for governed writes.
