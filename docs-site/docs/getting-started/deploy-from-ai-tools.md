---
title: Deploy from Claude Code, Codex & Cursor
description: Deploy to RunAgents without leaving your AI coding tool. Three paths — copilot shell, action plans, or direct CLI — all from your terminal.
---

# Deploy from Claude Code, Codex & Cursor

You wrote an agent. It works locally. Now you want it in production with identity propagation, policy enforcement, and approval workflows — **without opening a browser**.

This guide covers three paths, all terminal-native:

| Path | Best for | Command |
|------|----------|---------|
| [**Copilot shell**](#path-a-copilot-shell) | Quick interactive deploys | `runagents copilot` |
| [**Action plans**](#path-b-action-plans-with-claude-code-or-codex) | Repeatable, version-controlled deploys | `runagents action apply` |
| [**Direct CLI**](#path-c-direct-cli-deploy) | Simple agents, one liner | `runagents deploy` |

!!! tip "No console required"

    Every operation in this guide works entirely from the terminal. The [console](https://try.runagents.io) is optional — it gives you a UI to view runs, approve actions, and monitor agents, but you never need it to deploy.

---

## Prerequisites

**1. Get a RunAgents workspace**

Sign up at [try.runagents.io](https://try.runagents.io). You receive a workspace URL and API key.

**2. Install the CLI**

```bash
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
```

```bash
# Verify
runagents version
# runagents 1.1.1
```

**3. Configure**

```bash
runagents config set endpoint https://YOUR_WORKSPACE.try.runagents.io
runagents config set api-key ra_YOUR_API_KEY
runagents config set namespace default
```

Your API key is in the console under **Settings → API Keys**, or ask the copilot:

```bash
runagents copilot chat "where do I find my API key?"
```

---

## Path A: Copilot Shell

The fastest path. Type what you want — the copilot detects your code, proposes resources, and deploys after your confirmation.

```bash
runagents copilot
```

```
RunAgents Copilot — type a command or describe what you want

> deploy this folder as support-agent

Analyzing 3 source files in ./...
  ✓ Detected: stripe (https://api.stripe.com), slack (https://slack.com/api)
  ✓ Detected: openai gpt-4o-mini

I'll create the following:
  1. Register tool:  stripe   (https://api.stripe.com, OAuth2, Critical)
  2. Register tool:  slack    (https://slack.com/api, API Key, Open)
  3. Deploy agent:   support-agent (gpt-4o-mini)

Confirm? [y/n] y

  ✓ Tool registered: stripe
  ✓ Tool registered: slack
  ✓ Agent deployed:  support-agent (Running)

> test it: look up stripe customer alice@example.com

Invoking support-agent...
  → Tool call: stripe/v1/customers/search (200 OK)
  ✓ Response: Customer found — Alice Smith, plan: Pro
```

### Using the copilot from inside Claude Code

Add a `.claude/commands/deploy.md` to your project:

```markdown
Deploy the current agent to RunAgents:
1. Run `runagents copilot` in the terminal
2. Type: deploy this folder as [AGENT_NAME]
3. Confirm the proposed resources
```

Or just run it directly in the Claude Code terminal panel:

```bash
# Inside your Claude Code project
runagents copilot
> deploy this folder as my-agent
```

---

## Path B: Action Plans with Claude Code or Codex

The most powerful path for teams. Your AI tool generates a structured deployment plan, you review it, validate it, and apply it. Plans are JSON files you can commit to version control.

### Step 1: Export workspace state

```bash
runagents context export -o json > runagents-context.json
```

This snapshot includes all registered tools, model providers, agents, policies, and deploy drafts in your workspace.

### Step 2: Ask your AI tool to write the plan

=== "Claude Code"

    Open your project in Claude Code. The agent.py and runagents-context.json are both on disk. Ask Claude:

    ```
    I have an agent in agent.py that calls Stripe and Slack.
    Read runagents-context.json to see my current RunAgents workspace.

    Generate a file called plan.json that:
    1. Registers stripe as a tool (https://api.stripe.com, OAuth2, Critical access)
    2. Registers slack as a tool (https://slack.com/api, API Key, Open access)
    3. Deploys agent.py as "support-agent" using gpt-4o-mini

    Follow the RunAgents action plan schema:
    https://github.com/runagents-io/runagents/blob/main/docs-site/docs/cli/plan-schema.json
    ```

    Claude Code will write `plan.json` to your project. Example output:

    ```json
    {
      "plan_id": "deploy-support-agent",
      "continue_on_error": false,
      "actions": [
        {
          "id": "register-stripe",
          "type": "tool.upsert",
          "idempotency_key": "tool-stripe-v1",
          "params": {
            "name": "stripe",
            "spec": {
              "connection": { "baseUrl": "https://api.stripe.com" },
              "authType": "OAuth2",
              "accessMode": "Critical"
            }
          }
        },
        {
          "id": "register-slack",
          "type": "tool.upsert",
          "idempotency_key": "tool-slack-v1",
          "params": {
            "name": "slack",
            "spec": {
              "connection": { "baseUrl": "https://slack.com/api" },
              "authType": "ApiKey",
              "accessMode": "Open"
            }
          }
        },
        {
          "id": "deploy-agent",
          "type": "deploy.execute",
          "idempotency_key": "deploy-support-agent-v1",
          "params": {
            "agent_name": "support-agent",
            "source_files": { "agent.py": "<contents>" },
            "llm_configs": [{ "provider": "openai", "model": "gpt-4o-mini" }],
            "required_tools": ["stripe", "slack"]
          }
        }
      ]
    }
    ```

=== "OpenAI Codex"

    In the Codex web interface or API, include both files in context:

    ```
    Files: runagents-context.json, agent.py

    Generate a RunAgents action plan (plan.json) to:
    - Register stripe (https://api.stripe.com, OAuth2, Critical)
    - Register slack (https://slack.com/api, API Key, Open)
    - Deploy agent.py as "support-agent" using gpt-4o-mini

    Schema reference: https://github.com/runagents-io/runagents/blob/main/docs-site/docs/cli/plan-schema.json
    Each action needs: id, type, idempotency_key, params
    ```

=== "Cursor"

    Open both `agent.py` and `runagents-context.json` in Cursor. In the Composer:

    ```
    Using runagents-context.json as the current workspace state,
    create plan.json to deploy agent.py as "support-agent".
    Register stripe and slack tools first.
    Follow the RunAgents action plan schema.
    ```

    Cursor Composer will write the file directly to your project.

### Step 3: Validate before applying

```bash
runagents action validate --file plan.json
```

```
Plan: deploy-support-agent  (3 actions)

  ✓ tool.upsert         register-stripe       valid
  ✓ tool.upsert         register-slack        valid
  ✓ deploy.execute      deploy-agent          valid

All 3 actions valid. Ready to apply.
```

Validation checks required fields, schema correctness, and duplicate idempotency keys. **Nothing is created yet.**

### Step 4: Apply

```bash
runagents action apply --file plan.json
```

```
Applying plan: deploy-support-agent

  ✓ register-stripe      applied   (tool: stripe)
  ✓ register-slack       applied   (tool: slack)
  ✓ deploy-agent         applied   (agent: support-agent, status: Running)

3/3 actions applied successfully.
```

!!! tip "Idempotent — safe to re-run"
    Each action has an `idempotency_key`. Re-applying the same plan is safe — already-applied actions are skipped. Commit `plan.json` to version control and re-run on every release.

!!! tip "Automate in CI"
    ```bash
    # In your CI pipeline (GitHub Actions, etc.)
    - name: Deploy to RunAgents
      env:
        RUNAGENTS_ENDPOINT: ${{ secrets.RUNAGENTS_ENDPOINT }}
        RUNAGENTS_API_KEY: ${{ secrets.RUNAGENTS_API_KEY }}
      run: |
        runagents action validate --file plan.json
        runagents action apply --file plan.json
    ```

---

## Path C: Direct CLI Deploy

For simple agents where you know the tools and model upfront.

```bash
runagents deploy \
  --name support-agent \
  --file agent.py \
  --tool stripe \
  --tool slack \
  --model openai/gpt-4o-mini
```

```
Analyzing agent.py...
  Detected tools:      stripe, slack
  Detected LLM usage:  gpt-4o-mini
  Entry point:         agent.py

Deploying agent "support-agent"...
  ✓ Tool bound:      stripe (Open access)
  ✓ Tool bound:      slack  (Open access)
  ✓ Agent deployed:  support-agent (Running)
```

The `--tool` flag references tools already registered in your workspace. If a tool doesn't exist yet, register it first:

```bash
runagents tools create \
  --name stripe \
  --url https://api.stripe.com \
  --auth oauth2 \
  --access critical
```

---

## What Gets Created

Regardless of which path you use, the platform creates the same resources:

| Resource | What it is |
|----------|-----------|
| **Agent** | A running service with its own identity (service account) |
| **Policy bindings** | Access rules linking the agent to each tool |
| **Configuration** | Tool URLs, LLM gateway, model settings — injected as env vars |
| **Tool registrations** | Secure, policy-enforced routes to each external API |

Your agent code runs unchanged. No secrets, no API keys — all credentials are injected at the network layer.

---

## Check it's running

```bash
# Status
runagents agents get support-agent

# Tail recent runs
runagents runs list --agent support-agent

# View run events
runagents runs get run-XXXXX
```

Or open the [console](https://try.runagents.io) — navigate to **Agents → support-agent → Playground** — and send a test message.

---

## What changed vs running locally

| | Local | RunAgents |
|---|---|---|
| **API keys** | Hardcoded / `.env` | Injected at network layer — never in code |
| **Identity** | Yours | End-user identity flows through to every tool call |
| **Access control** | None | Policy checked on every outbound request |
| **High-risk actions** | Execute immediately | Paused for admin approval |
| **Audit trail** | None | Full log — user, agent, tool, timestamp, payload hash |

---

## Next Steps

<div class="grid cards" markdown>

-   :material-book-open-variant:{ .middle } **Action Plan Schema**

    Full JSON schema reference with all supported action types.

    [:octicons-arrow-right-24: plan-schema.json](../cli/action-plans.md)

-   :material-console-line:{ .middle } **CLI Commands**

    Full reference for every `runagents` command and flag.

    [:octicons-arrow-right-24: Commands](../cli/commands.md)

-   :material-shield-check-outline:{ .middle } **Approval Workflows**

    Configure Slack/PagerDuty notifications for high-risk tool calls.

    [:octicons-arrow-right-24: Approvals](../platform/approvals.md)

-   :material-chart-timeline-variant:{ .middle } **Run Observability**

    Monitor runs, view events, export audit logs.

    [:octicons-arrow-right-24: Run lifecycle](../operations/runs.md)

</div>
