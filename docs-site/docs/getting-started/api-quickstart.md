---
title: API Quickstart
description: Deploy your first AI agent programmatically using the RunAgents API.
---

# API Quickstart

Deploy your first agent programmatically using the RunAgents REST API. This guide walks through every step with curl — from seeding starter resources to deploying an agent and checking its runs.

**Base URL**: `https://api.runagents.io`

!!! info "Prerequisites"

    You need a RunAgents account and an API key. If you do not have an account yet, email [try@runagents.io](mailto:try@runagents.io) to request trial access.

---

## Step 1: Get Your API Key

Log in to the RunAgents console, navigate to **Settings**, and copy your API key. All API requests require this key in the `Authorization` header.

```bash
export RUNAGENTS_API_KEY="ra_live_abc123your-api-key-here"
```

---

## Step 2: Seed Starter Resources

Before deploying an agent, create the built-in Echo Tool and Playground LLM. This endpoint is idempotent — calling it multiple times is safe.

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/starter-kit \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json"
    ```

=== "Python"

    ```python
    import requests

    headers = {
        "Authorization": f"Bearer {RUNAGENTS_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post("https://api.runagents.io/api/starter-kit", headers=headers)
    print(resp.json())
    ```

**Response** `200 OK`:

```json
{
  "status": "ok",
  "tools_created": ["echo-tool"],
  "model_providers_created": ["playground-llm"]
}
```

This creates:

| Resource | Description |
|---|---|
| `echo-tool` | A built-in tool that echoes back messages. Open access, no API key required. |
| `playground-llm` | An OpenAI-compatible model provider (gpt-4o-mini). |

---

## Step 3: Analyze Your Agent Code

Submit your agent source files for analysis. The platform inspects the code using AST parsing and pattern detection to identify tool calls, LLM usage, secrets, and dependencies.

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/ingestion/analyze \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "files": {
          "agent.py": "import urllib.request\nimport json\n\ndef main():\n    tool_url = os.environ.get(\"TOOL_ECHO_TOOL_URL\", \"http://echo-tool\")\n    llm_url = os.environ.get(\"LLM_GATEWAY_URL\", \"http://llm-gateway\")\n\n    # Call echo tool\n    req = urllib.request.Request(\n        f\"{tool_url}/echo\",\n        data=json.dumps({\"message\": \"Hello from my agent!\"}).encode(),\n        headers={\"Content-Type\": \"application/json\"},\n        method=\"POST\"\n    )\n    resp = urllib.request.urlopen(req)\n    echo_result = json.loads(resp.read())\n\n    # Call LLM\n    llm_req = urllib.request.Request(\n        f\"{llm_url}/v1/chat/completions\",\n        data=json.dumps({\n            \"model\": \"gpt-4o-mini\",\n            \"messages\": [{\"role\": \"user\", \"content\": echo_result[\"echo\"]}]\n        }).encode(),\n        headers={\"Content-Type\": \"application/json\"},\n        method=\"POST\"\n    )\n    llm_resp = urllib.request.urlopen(llm_req)\n    print(json.loads(llm_resp.read()))\n\nif __name__ == \"__main__\":\n    main()\n"
        }
      }'
    ```

=== "Python"

    ```python
    agent_code = '''
    import urllib.request
    import json
    import os

    def main():
        tool_url = os.environ.get("TOOL_ECHO_TOOL_URL", "http://echo-tool")
        llm_url = os.environ.get("LLM_GATEWAY_URL", "http://llm-gateway")

        req = urllib.request.Request(
            f"{tool_url}/echo",
            data=json.dumps({"message": "Hello from my agent!"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        echo_result = json.loads(resp.read())

        llm_req = urllib.request.Request(
            f"{llm_url}/v1/chat/completions",
            data=json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": echo_result["echo"]}]
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        llm_resp = urllib.request.urlopen(llm_req)
        print(json.loads(llm_resp.read()))

    if __name__ == "__main__":
        main()
    '''

    resp = requests.post(
        "https://api.runagents.io/ingestion/analyze",
        headers=headers,
        json={"files": {"agent.py": agent_code}},
    )
    analysis = resp.json()
    print(json.dumps(analysis, indent=2))
    ```

**Response** `201 Created`:

```json
{
  "id": "analysis-8f3a2b1c",
  "tools": [
    {
      "name": "echo-tool",
      "detected_url_pattern": "TOOL_ECHO_TOOL_URL",
      "file": "agent.py",
      "line": 10
    }
  ],
  "model_providers": [],
  "model_usages": [
    {
      "role": "default",
      "model": "gpt-4o-mini",
      "variable_name": "LLM_GATEWAY_URL",
      "file": "agent.py",
      "line": 20
    }
  ],
  "secrets": [],
  "outbound_destinations": [],
  "detected_requirements": [],
  "entry_point": "agent.py",
  "system_prompt_suggestion": ""
}
```

The analysis tells you:

- The code calls a tool named `echo-tool` via the `TOOL_ECHO_TOOL_URL` environment variable
- It uses the LLM gateway with model `gpt-4o-mini`
- No secrets were detected in the source code

---

## Step 4: Deploy the Agent

Use the analysis results to deploy the agent. Map detected tools to registered tools and configure LLM providers.

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/deploy \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "hello-world",
        "files": {
          "agent.py": "import urllib.request\nimport json\nimport os\n\ndef main():\n    tool_url = os.environ.get(\"TOOL_ECHO_TOOL_URL\", \"http://echo-tool\")\n    llm_url = os.environ.get(\"LLM_GATEWAY_URL\", \"http://llm-gateway\")\n\n    req = urllib.request.Request(\n        f\"{tool_url}/echo\",\n        data=json.dumps({\"message\": \"Hello from my agent!\"}).encode(),\n        headers={\"Content-Type\": \"application/json\"},\n        method=\"POST\"\n    )\n    resp = urllib.request.urlopen(req)\n    echo_result = json.loads(resp.read())\n\n    llm_req = urllib.request.Request(\n        f\"{llm_url}/v1/chat/completions\",\n        data=json.dumps({\n            \"model\": \"gpt-4o-mini\",\n            \"messages\": [{\"role\": \"user\", \"content\": echo_result[\"echo\"]}]\n        }).encode(),\n        headers={\"Content-Type\": \"application/json\"},\n        method=\"POST\"\n    )\n    llm_resp = urllib.request.urlopen(llm_req)\n    print(json.loads(llm_resp.read()))\n\nif __name__ == \"__main__\":\n    main()\n"
        },
        "tools_to_create": [],
        "required_tools": ["echo-tool"],
        "llm_configs": [
          {
            "role": "default",
            "provider": "openai",
            "model": "gpt-4o-mini"
          }
        ],
        "identity_provider": null
      }'
    ```

=== "Python"

    ```python
    deploy_payload = {
        "name": "hello-world",
        "files": {"agent.py": agent_code},
        "tools_to_create": [],
        "required_tools": ["echo-tool"],
        "llm_configs": [
            {
                "role": "default",
                "provider": "openai",
                "model": "gpt-4o-mini",
            }
        ],
        "identity_provider": None,
    }

    resp = requests.post(
        "https://api.runagents.io/api/deploy",
        headers=headers,
        json=deploy_payload,
    )
    print(resp.json())
    ```

**Response** `200 OK`:

```json
{
  "status": "ok",
  "agent": {
    "name": "hello-world",
    "namespace": "default",
    "status": "Pending"
  },
  "tools_created": [],
  "policies_created": [
    "hello-world-echo-tool-auto"
  ]
}
```

!!! success "Your agent is deployed"

    The platform created the agent, wired it to the Echo Tool, and auto-generated access policies. The agent will transition from `Pending` to `Running` within a few seconds.

### Deploy Request Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Agent name. Must be unique within your project. |
| `files` | object | Map of filename to source code content. |
| `tools_to_create` | array | New tool definitions to register alongside the agent. |
| `required_tools` | array | Names of existing tools the agent needs access to. |
| `llm_configs` | array | LLM provider configurations. Each has `role`, `provider`, and `model`. |
| `identity_provider` | string or null | Name of the identity provider for client authentication. |

---

## Step 5: List Your Agents

Verify the agent was created and check its status.

=== "curl"

    ```bash
    curl -s https://api.runagents.io/api/agents \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq .
    ```

=== "Python"

    ```python
    resp = requests.get("https://api.runagents.io/api/agents", headers=headers)
    for agent in resp.json():
        print(f"{agent['name']}: {agent['status']}")
    ```

**Response** `200 OK`:

```json
[
  {
    "name": "hello-world",
    "namespace": "default",
    "status": "Running",
    "required_tools": ["echo-tool"],
    "llm_model": "gpt-4o-mini",
    "created_at": "2026-02-23T10:15:30Z"
  }
]
```

---

## Step 6: Check Runs

Once the agent starts processing requests, you can view its run history.

=== "curl"

    ```bash
    curl -s https://api.runagents.io/runs \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq .
    ```

=== "Python"

    ```python
    resp = requests.get("https://api.runagents.io/runs", headers=headers)
    for run in resp.json():
        print(f"Run {run['id']}: {run['state']} ({run['agent']})")
    ```

**Response** `200 OK`:

```json
[
  {
    "id": "run-7f2a9c3e",
    "agent": "hello-world",
    "state": "COMPLETED",
    "created_at": "2026-02-23T10:16:45Z",
    "updated_at": "2026-02-23T10:16:47Z"
  }
]
```

### Run States

| State | Description |
|---|---|
| `RUNNING` | The agent is actively processing. |
| `PAUSED_APPROVAL` | The agent tried to call a tool that requires approval. Waiting for admin. |
| `COMPLETED` | The run finished successfully. |
| `FAILED` | The run encountered an error. |

To view events for a specific run:

```bash
curl -s https://api.runagents.io/runs/run-7f2a9c3e/events \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq .
```

---

## Full Example Script

Here is the complete workflow in a single script:

```bash
#!/bin/bash
set -euo pipefail

API="https://api.runagents.io"
TOKEN="ra_live_abc123your-api-key-here"
AUTH="Authorization: Bearer $TOKEN"

echo "==> Seeding starter resources..."
curl -s -X POST "$API/api/starter-kit" \
  -H "$AUTH" -H "Content-Type: application/json" | jq .

echo "==> Deploying hello-world agent..."
curl -s -X POST "$API/api/deploy" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world",
    "files": {
      "agent.py": "import urllib.request, json, os\n\ndef main():\n    tool = os.environ[\"TOOL_ECHO_TOOL_URL\"]\n    llm = os.environ[\"LLM_GATEWAY_URL\"]\n    req = urllib.request.Request(f\"{tool}/echo\", data=json.dumps({\"message\":\"hi\"}).encode(), headers={\"Content-Type\":\"application/json\"}, method=\"POST\")\n    print(json.loads(urllib.request.urlopen(req).read()))\n\nif __name__==\"__main__\": main()"
    },
    "required_tools": ["echo-tool"],
    "tools_to_create": [],
    "llm_configs": [{"role":"default","provider":"openai","model":"gpt-4o-mini"}],
    "identity_provider": null
  }' | jq .

echo "==> Waiting for agent to start..."
sleep 5

echo "==> Listing agents..."
curl -s "$API/api/agents" -H "$AUTH" | jq .

echo "==> Listing runs..."
curl -s "$API/runs" -H "$AUTH" | jq .

echo "Done."
```

---

## Next Steps

- [**CLI Quickstart**](cli-quickstart.md) -- Do the same from your terminal with the RunAgents CLI
- [**API Reference**](../api/overview.md) -- Full endpoint documentation
- [**Registering Tools**](../platform/registering-tools.md) -- Add your own external APIs and SaaS services
- [**Policy Model**](../concepts/policy-model.md) -- Understand how access control works

!!! tip "Need help?"

    Email [try@runagents.io](mailto:try@runagents.io) and we will get you set up.
