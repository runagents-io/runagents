---
name: runagents-catalog-deploy
description: Use when deploying or adapting a RunAgents catalog agent, especially production-shaped templates like the Google Workspace assistant. Helps choose the right catalog entry, map tools, identity providers, models, and policies, deploy safely, and validate the resulting runs.
---

# RunAgents Catalog Deploy

Use this skill when the goal is to launch a RunAgents agent from the catalog instead of starting from a blank `agent.py`.

## Use this skill for

- deploying a catalog agent into a workspace
- adapting a catalog agent to a customer environment
- choosing between a Hello World quickstart and a production-shaped starter
- validating that the deployed agent is actually usable after deployment

## Workflow

1. Prefer the catalog when the user wants a realistic workflow.
   The best flagship example is the Google Workspace assistant because it exercises tools, delegated identity, OAuth consent, approvals, resumed execution, and multi-surface usage.

2. Inventory the deployment prerequisites before deploying.
   Check for:
   - required tools
   - required model providers
   - required identity providers
   - required policies or approval rules
   - any messaging or app surface the agent will sit behind

3. Keep the deployment path explicit.
   Use one of these:
   - RunAgents console deploy flow
   - `runagents deploy` style CLI flow
   - RunAgents MCP tools from Codex / Claude Code / Cursor
   - public Deploy API

4. Wire governance before testing write actions.
   For agents that send email, create calendar events, mutate CRM records, or post messages, ensure the tool capabilities and approval-required policy are in place before testing.

5. Validate the deployment with a real run, not just a successful deploy event.
   Check:
   - agent status is healthy
   - latest runs are visible
   - tool auth succeeds
   - approvals or consents show up where expected
   - the final user-visible action actually completes

## Strong defaults

- Prefer catalog agents over toy quickstarts when the user is evaluating production readiness.
- Treat Google Workspace assistant as the best first example for governed write flows.
- If the interface is external, remind yourself that the interface can be anywhere: web app, WhatsApp, Slack, internal portal, or custom client.
- Always separate deploy success from workflow success.

## Example prompt

Use `$runagents-catalog-deploy` to deploy the Google Workspace assistant, wire its prerequisites, and tell me what still needs to be configured before a real calendar write test.
