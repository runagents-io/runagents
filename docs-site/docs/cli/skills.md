---
title: RunAgents Skills
description: First-party workflow skills for Codex-style assistants and other AI coding tools working with RunAgents.
---

# RunAgents Skills

RunAgents ships with a public skills library for AI coding assistants that need more than generic project context.

Source folder: [`skills/` on GitHub](https://github.com/runagents-io/runagents/tree/main/skills).

These skills are designed to feel closer to workflow packs than prompt snippets. Each one captures a specific RunAgents job to be done: deploying catalog agents, onboarding governed tools, designing approval policy, debugging runs, or wiring RunAgents behind interfaces such as WhatsApp, Slack, web apps, and internal portals.

## Why skills instead of only templates?

The template files in [AI Assistant Setup](ai-assistant-setup.md) are still useful. They teach an assistant the basic RunAgents commands and project structure.

Skills solve a different problem: they give the assistant a reusable operating workflow for one specific class of RunAgents work.

That means:

- less generic prompting
- more consistent outputs
- safer production workflows
- better handoff across operators and assistants

## Available skills

| Skill | Use it for |
|------|-------------|
| `runagents-catalog-deploy` | Deploy and adapt production-shaped catalog agents such as the Google Workspace assistant |
| `runagents-tool-onboarding` | Register tools with the right auth model, capabilities, and scopes |
| `runagents-approval-policy` | Design approval-required policy and choose the right scope |
| `runagents-run-debugging` | Trace paused, approval-blocked, consent-blocked, and failed runs |
| `runagents-surface-integration` | Connect RunAgents to web apps, WhatsApp, Slack, internal portals, and other interfaces |

## Installing skills for Codex-style assistants

Clone the repository and copy the skills you want into your local skills directory:

```bash
git clone https://github.com/runagents-io/runagents.git
mkdir -p ~/.codex/skills
cp -R runagents/skills/runagents-approval-policy ~/.codex/skills/
cp -R runagents/skills/runagents-surface-integration ~/.codex/skills/
```

Then invoke them explicitly in your prompt, for example:

```text
Use $runagents-approval-policy to design a safe approval flow for this Google Workspace assistant.
```

## Using the same skills with other assistants

If your assistant does not support native skill folders, you can still use the same material.

Recommended options:

1. paste the relevant `SKILL.md` into project context
2. turn the workflow into a project rule file such as `CLAUDE.md`, `.cursorrules`, or `AGENTS.md`
3. pair it with the RunAgents MCP server so the assistant can act on live workspace data

## Recommended starting sequence

If you want the strongest first production path, use the skills in this order:

1. `runagents-catalog-deploy`
2. `runagents-tool-onboarding`
3. `runagents-approval-policy`
4. `runagents-surface-integration`
5. `runagents-run-debugging`

That mirrors a real rollout path:

- deploy a production-shaped agent
- wire tools and identity
- govern writes
- connect the user-facing surface
- debug live behavior with evidence

## Strong first example: Google Workspace assistant

The Google Workspace assistant is the best first example for these skills because it combines:

- delegated-user OAuth
- policy-controlled writes
- approval and consent flows
- resumed execution
- multi-surface usage
- real business actions such as email, calendar, and document work

## Related

- [AI Assistant Setup](ai-assistant-setup.md)
- [External Assistants](external-assistants.md)
- [Agent Catalog](../platform/agent-catalog.md)
- [Approvals](../platform/approvals.md)
- [Run Lifecycle](../operations/runs.md)
