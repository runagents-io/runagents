# RunAgents Skills

This folder contains first-party workflow skills for AI coding assistants working with RunAgents.

These skills are external-facing workflow packs. They are written so customers, partners, and internal teams can reuse the same material across Codex, Claude Code, Cursor, and similar assistants without depending on private infrastructure assumptions.

## Included skills

### Build

- `runagents-agent-authoring` — write or refactor platform-native RunAgents agents
- `runagents-action-plan-workflow` — drive validate-then-apply assistant workflows with deterministic plans

### Wire

- `runagents-catalog-deploy` — deploy and adapt production-shaped catalog agents such as the Google Workspace assistant
- `runagents-tool-onboarding` — register tools with the right capabilities, auth model, and least-privilege scopes
- `runagents-model-provider-setup` — configure model providers and role-based gateway wiring
- `runagents-identity-provider-setup` — configure end-user identity propagation and delegated-user workflows

### Govern

- `runagents-approval-policy` — design approval-required policies and choose the right approval scope
- `runagents-oauth-consent-debugging` — debug delegated OAuth and consent flows

### Operate

- `runagents-run-debugging` — debug paused, approval-blocked, consent-blocked, and failed runs
- `runagents-observability-triage` — turn dashboard symptoms into operational root causes

### Interface

- `runagents-surface-integration` — connect RunAgents to web apps, WhatsApp, Slack, internal portals, and other interfaces

### Connectors

- `runagents-policy-connector` — expose policy state and approval-required posture to external systems
- `runagents-approval-connector` — integrate approvals with custom inboxes, messaging apps, and internal workflows
- `runagents-observability-connector` — export runs and event signals into external observability and analytics systems

## Using these skills with Codex and skill-native environments

1. Copy the skill folder you want into your local skills directory.
2. Invoke it explicitly in your prompt, for example: `$runagents-approval-policy`.
3. Pair it with the RunAgents MCP server when you want live workspace access.

Example:

```bash
mkdir -p ~/.codex/skills
cp -R skills/runagents-approval-policy ~/.codex/skills/
```

## Using these skills with Claude Code

Claude Code can use the same public skills through `CLAUDE.md` imports or project slash commands.

Example `CLAUDE.md` import:

```md
@skills/runagents-approval-policy/SKILL.md
@skills/runagents-run-debugging/SKILL.md
```

Example project command:

```bash
mkdir -p .claude/commands/runagents
cat > .claude/commands/runagents/run-debug.md <<'EOF'
Review @skills/runagents-run-debugging/SKILL.md and apply it to: $ARGUMENTS
EOF
```

## Using these skills with Cursor and other assistants

If your assistant does not support skills natively:

1. open the relevant `SKILL.md`
2. paste the workflow into your project context, system instructions, or repo rules file
3. combine it with the RunAgents CLI templates and MCP server from `docs.runagents.io`

## Recommended starting point

If you are new to RunAgents, start with:

1. `runagents-catalog-deploy`
2. `runagents-tool-onboarding`
3. `runagents-approval-policy`
4. `runagents-surface-integration`
5. `runagents-run-debugging`

That sequence maps cleanly to the most common production path:

- deploy a catalog agent
- wire tools and identity
- govern writes with approvals
- connect the user-facing surface
- debug live behavior with evidence
