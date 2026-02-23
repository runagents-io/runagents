# Agents API

Manage deployed AI agents. Use the [Deploy API](deploy.md) to create new agents, and this API to list, inspect, and delete them.

---

## List Agents

<span class="method-get">GET</span> <span class="endpoint">/api/agents</span>

Returns all deployed agents across all namespaces.

=== "curl"

    ```bash
    curl https://api.runagents.io/api/agents \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

=== "Python"

    ```python
    import requests

    resp = requests.get(
        "https://api.runagents.io/api/agents",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    agents = resp.json()
    ```

### Response (200 OK)

```json
[
  {
    "name": "payment-agent",
    "namespace": "agent-system",
    "labels": {
      "platform.ai/identity-provider": "google-oidc"
    },
    "spec": {
      "image": "registry.runagents.io/payment-agent:a1b2c3",
      "systemPrompt": "You are a payment processing assistant.",
      "requiredTools": [
        {"name": "stripe-api"}
      ],
      "llmConfig": {
        "provider": "openai",
        "model": "gpt-4o-mini"
      },
      "env": [
        {"name": "LLM_MODEL", "value": "gpt-4o-mini"},
        {"name": "LLM_PROVIDER", "value": "openai"}
      ]
    },
    "status": {
      "phase": "Running",
      "message": ""
    }
  }
]
```

---

## Get Agent Details

<span class="method-get">GET</span> <span class="endpoint">/api/agents/:namespace/:name</span>

Retrieve details for a specific agent.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | string | Agent namespace |
| `name` | string | Agent name |

=== "curl"

    ```bash
    curl https://api.runagents.io/api/agents/agent-system/payment-agent \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "name": "payment-agent",
  "namespace": "agent-system",
  "spec": {
    "image": "registry.runagents.io/payment-agent:a1b2c3",
    "systemPrompt": "You are a payment processing assistant.",
    "requiredTools": [
      {"name": "stripe-api"}
    ],
    "llmConfig": {
      "provider": "openai",
      "model": "gpt-4o-mini"
    },
    "env": [
      {"name": "LLM_MODEL", "value": "gpt-4o-mini"},
      {"name": "LLM_PROVIDER", "value": "openai"}
    ]
  },
  "status": {
    "phase": "Running",
    "message": ""
  }
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `400` | `path must be /api/agents/{namespace}/{name}` | Invalid path format |
| `404` | `agent {namespace}/{name} not found` | Agent does not exist |

---

## Delete an Agent

<span class="method-delete">DELETE</span> <span class="endpoint">/api/agents/:namespace/:name</span>

Delete an agent and its associated resources.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | string | Agent namespace |
| `name` | string | Agent name |

=== "curl"

    ```bash
    curl -X DELETE https://api.runagents.io/api/agents/agent-system/payment-agent \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "status": "deleted"
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `agent {namespace}/{name} not found` | Agent does not exist |

---

## Invoke an Agent

<span class="method-post">POST</span> <span class="endpoint">/api/agents/:namespace/:name/invoke</span>

Send a message to a running agent. The request is proxied to the agent's `/invoke` endpoint.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | string | Agent namespace |
| `name` | string | Agent name |

### Request Body

The request body is forwarded directly to the agent. The format depends on the agent's implementation, but a typical payload is:

```json
{
  "message": "What are the recent charges?",
  "conversation_id": "conv-123"
}
```

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/agents/agent-system/payment-agent/invoke \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"message": "What are the recent charges?"}'
    ```

### Response

The response is returned directly from the agent. Status code and body format are determined by the agent's implementation.

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `agent {namespace}/{name} not found` | Agent does not exist |
| `502` | `failed to reach agent: ...` | Agent is not responding |

---

## Agent Object Reference

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent name |
| `namespace` | string | Namespace |
| `labels` | object | Key-value labels (e.g., identity provider association) |
| `spec.image` | string | Container image URI |
| `spec.systemPrompt` | string | System prompt injected into the agent's LLM context |
| `spec.requiredTools` | object[] | List of tool references (`{"name": "..."}`) |
| `spec.llmConfig` | object | Primary LLM configuration (`provider`, `model`) |
| `spec.env` | object[] | Environment variables (`name`, `value`) |
| `status.phase` | string | Current phase: `Pending`, `Running`, or `Failed` |
| `status.message` | string | Human-readable status detail |

### Status Phases

| Phase | Description |
|-------|-------------|
| `Pending` | Agent is being provisioned |
| `Running` | Agent is deployed and healthy |
| `Failed` | Agent failed to start or encountered an error |
