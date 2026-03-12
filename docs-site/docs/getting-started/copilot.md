---
title: RunAgents Copilot
description: Deploy and manage AI agents using natural language — in your terminal or the console sidebar.
---

# RunAgents Copilot

Copilot lets you manage the entire RunAgents platform in natural language. Describe what you want to deploy, and Copilot figures out the steps, proposes the resources, and creates them after your confirmation.

---

## Console Copilot

Open the copilot panel from the **?** button in the console sidebar on any page.

```
You: deploy a Stripe customer lookup agent

Copilot: I'll set up the following:
  1. Register tool: stripe (https://api.stripe.com, OAuth2)
  2. Deploy agent: stripe-lookup with gpt-4o-mini

  [Confirm] [Skip]
```

**Reads only** (list tools, check runs, view billing) execute instantly. **Mutations** (create tool, deploy agent, approve action) always show a confirmation card before executing.

Configure the model in **Settings > Copilot**. Requires an OpenAI API key.

---

## CLI Copilot

Interactive terminal session — ideal for developers who prefer the command line.

### Install

```bash
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
```

### Configure

```bash
runagents config set endpoint https://your-workspace.try.runagents.io
runagents config set api-key YOUR_API_KEY
runagents config set namespace default
```

### Start a session

```bash
runagents copilot
```

```
RunAgents Copilot v1.1.1 — type "exit" to quit, "help" for commands

> deploy this folder as billing-agent

Analyzing source files in ./ ...
  Detected tools:    stripe (https://api.stripe.com)
  Detected model:    gpt-4o-mini (openai)
  Entry point:       agent.py

I'll create:
  1. Register tool: stripe
  2. Deploy agent: billing-agent

[Confirm? y/n] y

  ✓ Tool created: stripe
  ✓ Agent deployed: billing-agent (Running)

> what tools do I have?

You have 3 registered tools:
  • echo-tool (Internal, Restricted posture)
  • stripe     (External, OAuth2)
  • slack      (External, API Key)
```

### Quick commands

| What to type | What happens |
|---|---|
| `deploy this folder as agent-name` | Analyzes current directory and deploys |
| `deploy draft <id> as agent-name` | Deploys from a saved draft |
| `what tools do I have?` | Lists registered tools |
| `list my running agents` | Shows agents and status |
| `approve action <id>` | Approves a blocked action |
| `check my billing` | Shows plan status and usage |

### Check readiness

```bash
runagents copilot doctor
```

Runs local + API connectivity checks and reports what's configured.

---

## Single-shot commands

Don't want an interactive session? Use `copilot chat` for one-off questions:

```bash
runagents copilot chat "how do I register a Stripe tool?"
```

---

## Project session memory

The CLI remembers context within a project directory. Create `.runagents/project.json` to persist agent name and tool preferences across sessions:

```json
{
  "agent_name": "billing-agent",
  "preferred_tools": ["stripe", "slack"],
  "default_model": "openai/gpt-4o-mini"
}
```

---

## What's Next

- [External Assistants (Claude Code / Codex)](../cli/external-assistants.md) — use your AI coding tool instead of the built-in copilot
- [Action Plans](../cli/action-plans.md) — generate and apply deterministic change plans
- [CLI Commands Reference](../cli/commands.md) — full list of all commands
