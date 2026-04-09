---
title: RunAgents Skills
description: First-party workflow skills for Codex, Claude Code, Cursor, and other AI coding assistants working with RunAgents.
---

# RunAgents Skills

RunAgents ships with a public skills library for AI coding assistants that need more than generic project context.

Source folder: [`skills/` on GitHub](https://github.com/runagents-io/runagents/tree/main/skills).

These skills are external-facing workflow packs. They are written to be reusable across customer environments and to avoid private infrastructure assumptions. Each one captures a specific RunAgents job to be done: deploying catalog agents, onboarding governed tools, designing approval policy, debugging runs, or wiring RunAgents behind interfaces such as WhatsApp, Slack, web apps, and internal portals.

## Why skills instead of only templates?

The template files in [AI Assistant Setup](ai-assistant-setup.md) are still useful. They teach an assistant the basic RunAgents commands and project structure.

Skills solve a different problem: they give the assistant a reusable operating workflow for one specific class of RunAgents work.

That means:

- less generic prompting
- more consistent outputs
- safer production workflows
- better handoff across operators and assistants

## Design principles

The public RunAgents skills library is designed to be:

- **assistant-agnostic** — usable with Codex, Claude Code, Cursor, and similar tools
- **external-facing** — written for customer and partner environments, not only internal operators
- **workflow-scoped** — each skill solves one concrete RunAgents job to be done
- **composable** — skills can be paired with templates, MCP tools, and action plans
- **platform-aware** — they assume RunAgents owns identity propagation, policy, approvals, consent, and tool auth

## Coverage review

The current library is broad across the core RunAgents lifecycle:

- **Build** — authoring agents and plan-driven changes
- **Wire** — catalog deployment, tools, identity providers, and model providers
- **Govern** — approval policy and OAuth consent debugging
- **Operate** — run debugging and observability triage
- **Interface** — web, WhatsApp, Slack, internal portals, and other user-facing surfaces
- **Connectors** — policy, approval, and observability integrations with external systems

That is a strong first-party baseline for public use. The highest-value future additions would be self-hosted rollout, org-wide governance rollout, and incident-response playbooks, but the current set already covers the most common external deployment and operations paths.

## Available skills

### Build

| Skill | Use it for |
|------|-------------|
| `runagents-agent-authoring` | Write or refactor platform-native RunAgents agents |
| `runagents-action-plan-workflow` | Drive validate-then-apply assistant workflows with deterministic plans |

### Wire

| Skill | Use it for |
|------|-------------|
| `runagents-catalog-deploy` | Deploy and adapt production-shaped catalog agents such as the Google Workspace assistant |
| `runagents-tool-onboarding` | Register tools with the right auth model, capabilities, and scopes |
| `runagents-model-provider-setup` | Configure model providers and role-based gateway wiring |
| `runagents-identity-provider-setup` | Configure end-user identity propagation and delegated-user workflows |

### Govern

| Skill | Use it for |
|------|-------------|
| `runagents-approval-policy` | Design approval-required policy and choose the right scope |
| `runagents-oauth-consent-debugging` | Debug delegated OAuth, scopes, callbacks, and consent loops |

### Operate

| Skill | Use it for |
|------|-------------|
| `runagents-run-debugging` | Trace paused, approval-blocked, consent-blocked, and failed runs |
| `runagents-observability-triage` | Turn dashboard symptoms into operational root causes |

### Interface

| Skill | Use it for |
|------|-------------|
| `runagents-surface-integration` | Connect RunAgents to web apps, WhatsApp, Slack, internal portals, and other interfaces |

### Connectors

| Skill | Use it for |
|------|-------------|
| `runagents-policy-connector` | Expose policy state and approval-required posture to external systems |
| `runagents-approval-connector` | Integrate approvals with custom inboxes, messaging apps, and internal workflows |
| `runagents-observability-connector` | Export runs and event signals into external observability and analytics systems |

## Use with Codex and skill-native environments

If your assistant supports local skill folders, clone the repository and copy the skills you want into your local skills directory:

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

## Use with Claude Code

Claude Code does not use the same local skill-folder format as Codex, but the public RunAgents skills still map cleanly into Claude Code using project memory and custom slash commands.

### Option 1: Import a skill into `CLAUDE.md`

```md
# RunAgents workflows
@skills/runagents-approval-policy/SKILL.md
@skills/runagents-surface-integration/SKILL.md
```

This works well when you want those workflows available throughout a project.

### Option 2: Create project slash commands

```bash
mkdir -p .claude/commands/runagents
cat > .claude/commands/runagents/approval-policy.md <<'EOF'
Review @skills/runagents-approval-policy/SKILL.md and apply it to this request: $ARGUMENTS
EOF
```

Then use it inside Claude Code like:

```text
/runagents/approval-policy Design approvals for Google Workspace calendar writes
```

## Use with Cursor and other assistants

If your assistant does not support native skill folders, you can still use the same material.

Recommended options:

1. paste the relevant `SKILL.md` into project context
2. turn the workflow into a project rule file such as `CLAUDE.md`, `.cursorrules`, or `AGENTS.md`
3. pair it with the RunAgents MCP server so the assistant can act on live workspace data

## Recommended starting sequence

If you want the strongest first production path, use the skills in this order:

1. `runagents-catalog-deploy`
2. `runagents-tool-onboarding`
3. `runagents-identity-provider-setup`
4. `runagents-model-provider-setup`
5. `runagents-approval-policy`
6. `runagents-surface-integration`
7. `runagents-run-debugging`

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
