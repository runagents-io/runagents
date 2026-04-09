---
title: CLI Quickstart
description: Install the RunAgents CLI, configure your workspace, and deploy your first agent from terminal.
---

# CLI Quickstart

This walkthrough uses the current Go CLI command set and output shape.

---

## Step 1: Install

```bash
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
runagents version
```

---

## Step 2: Configure

```bash
runagents config set endpoint https://your-workspace.try.runagents.io
runagents config set api-key ra_ws_your_workspace_key
runagents config set namespace default
runagents config get
```

---

## Step 3: Seed Starter Resources

```bash
runagents starter-kit
```

This creates starter resources (`echo-tool`, `playground-llm`) if missing.

---

## Step 4: Create Agent File

Create `agent.py`:

```python
def handler(request):
    message = request.get("message", "")
    return {"response": f"hello: {message}"}
```

---

## Step 5: Deploy

```bash
runagents deploy \
  --name hello-world \
  --file agent.py \
  --tool echo-tool \
  --model openai/gpt-4o-mini
```

Notes:

- `runagents deploy` maps to `POST /api/deploy`.
- For tool-call authorization, bind policies via console deploy flow, API (`policies` field), or action plans.

---

## Step 6: Verify Agent

```bash
runagents agents list
runagents agents get default hello-world
```

---

## Step 7: Inspect Runs

```bash
runagents runs list --agent hello-world
runagents runs get <run-id>
runagents runs events <run-id>
```

---

## Step 8: Approvals (When Triggered)

If a policy rule returns `approval_required`, use:

```bash
runagents approvals list
runagents approvals approve <request-id>
# or
runagents approvals reject <request-id>
```

---

## Production-oriented path: deploy from the catalog

The quickest first-run path is still Hello World, but many teams want to validate a real workflow next.

A strong next step is deploying a catalog agent such as the Google Workspace assistant. That path is better when you want to test:

- delegated-user OAuth
- policy-controlled writes
- approval-required operations
- pause and resume behavior across real tools

Example:

```bash
runagents catalog list --search google
runagents catalog show google-workspace-assistant-agent
runagents catalog deploy google-workspace-assistant-agent \
  --name google-workspace-assistant-agent \
  --tool email \
  --tool calendar \
  --tool drive \
  --tool docs \
  --tool sheets \
  --tool tasks \
  --tool keep \
  --policy workspace-write-approval \
  --identity-provider google-oidc
```

See [Agent Catalog](../platform/agent-catalog.md) for the recommended production-style path.

---

## Useful Commands

```bash
runagents tools list
runagents tools get echo-tool
runagents models list
runagents context export -o json
```

---

## Next Steps

- [CLI Commands](../cli/commands.md)
- [Action Plans](../cli/action-plans.md)
- [Policy Model](../concepts/policy-model.md)
- [Approvals](../platform/approvals.md)
