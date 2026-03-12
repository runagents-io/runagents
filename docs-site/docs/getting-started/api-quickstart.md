---
title: API Quickstart
description: Deploy your first agent programmatically with the RunAgents API.
---

# API Quickstart

This quickstart deploys a simple agent via API and wires policy explicitly so tool calls are authorized from day one.

Base URL examples below use `https://api.runagents.io`.

---

## Step 1: Set API Key

```bash
export RUNAGENTS_API_KEY="ra_ws_your_workspace_key"
export API="https://api.runagents.io"
```

---

## Step 2: Seed Starter Resources

```bash
curl -X POST "$API/api/starter-kit" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json"
```

Example response (`201`):

```json
{
  "tool_created": "echo-tool",
  "model_provider_created": "playground-llm"
}
```

---

## Step 3: Create A Simple Policy

```bash
curl -X POST "$API/api/policies" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-echo-policy",
    "spec": {
      "policies": [
        {
          "permission": "allow",
          "resource": "http://governance.agent-system.svc:8092/*",
          "operations": ["GET", "POST"]
        }
      ]
    }
  }'
```

---

## Step 4: Deploy Agent With Policy Binding

```bash
curl -X POST "$API/api/deploy" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "hello-world",
    "source_files": {
      "agent.py": "def handler(request):\n    return {\"response\": \"hello from runagents\"}"
    },
    "entry_point": "agent.py",
    "required_tools": ["echo-tool"],
    "llm_configs": [
      {"provider": "openai", "model": "gpt-4o-mini", "role": "chat"}
    ],
    "policies": ["hello-echo-policy"]
  }'
```

Example response (`201`):

```json
{
  "agent": "hello-world",
  "namespace": "default",
  "tools_created": [],
  "execution_mode": "INSTANT_RUNTIME",
  "build_required": false
}
```

---

## Step 5: Verify Deployment

```bash
curl -s "$API/api/agents" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq .
```

Look for your agent transitioning to `Running`.

---

## Step 6: Check Runs

```bash
curl -s "$API/runs" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq .
```

Run states you will commonly see:

- `RUNNING`
- `PAUSED_APPROVAL`
- `COMPLETED`
- `FAILED`

---

## Step 7: Handle Approvals (If Triggered)

If a policy rule resolves to `approval_required`, approve via:

```bash
curl -s "$API/governance/requests?status=PENDING" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq .

curl -X POST "$API/governance/requests/<request-id>/approve" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Next Steps

- [Deploy API](../api/deploy.md)
- [Tools API](../api/tools.md)
- [Approvals API](../api/approvals.md)
- [Policy Model](../concepts/policy-model.md)
