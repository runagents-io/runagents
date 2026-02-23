# Deploy API

The Deploy API is the primary endpoint for deploying agents programmatically. It handles tool registration, image building, and agent creation in a single call.

---

## Deploy an Agent

<span class="method-post">POST</span> <span class="endpoint">/api/deploy</span>

Deploy a new agent or update an existing one. This endpoint is **idempotent** -- re-deploying with the same name updates the existing agent.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_name` | string | Yes | Unique name for the agent |
| `image` | string | No | Pre-built container image URI. Required if `source_files` is not provided |
| `source_files` | object | No | Map of filename to source code. Triggers server-side build if `image` is not provided |
| `system_prompt` | string | No | System prompt for the agent's LLM context |
| `required_tools` | string[] | No | Names of existing tools the agent needs access to |
| `tools_to_create` | object[] | No | New tools to register as part of this deployment |
| `llm_configs` | object[] | No | LLM model configurations (supports multi-model) |
| `llm_config` | object | No | Single LLM config (use `llm_configs` for multi-model) |
| `env` | object[] | No | Environment variables to inject into the agent |
| `requirements` | string | No | Python requirements (pip format) |
| `entry_point` | string | No | Entry point file for the agent |
| `framework` | string | No | Agent framework (e.g., `langchain`, `openai`) |
| `identity_provider` | string | No | Name of an existing identity provider to associate |

#### Tool Object (`tools_to_create`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique tool name |
| `description` | string | No | Human-readable description |
| `base_url` | string | Yes | Tool endpoint URL |
| `auth_type` | string | No | Authentication type: `None`, `APIKey`, `OAuth2`. Defaults to `None` |
| `port` | integer | No | Target port. Defaults to `443` |
| `scheme` | string | No | Protocol: `HTTP` or `HTTPS`. Defaults to `HTTPS` |

#### LLM Config Object (`llm_configs`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Provider name: `openai`, `anthropic`, `bedrock`, `ollama` |
| `model` | string | Yes | Model identifier (e.g., `gpt-4o-mini`) |
| `role` | string | No | Model role: `chat` (default), `embedding`, `classify`, `reranking` |

#### Env Var Object (`env`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Environment variable name |
| `value` | string | Yes | Environment variable value |

### Example: Deploy with source code and new tools

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/deploy \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "agent_name": "payment-agent",
        "source_files": {
          "agent.py": "import requests\nimport openai\n\nclient = openai.OpenAI()\n\ndef run():\n    response = requests.get(\"https://api.stripe.com/v1/charges\")\n    return response.json()\n\nif __name__ == \"__main__\":\n    run()"
        },
        "system_prompt": "You are a payment processing assistant.",
        "tools_to_create": [
          {
            "name": "stripe-api",
            "description": "Stripe payments API",
            "base_url": "https://api.stripe.com",
            "auth_type": "APIKey"
          }
        ],
        "required_tools": ["stripe-api"],
        "llm_configs": [
          {
            "role": "chat",
            "provider": "openai",
            "model": "gpt-4o-mini"
          }
        ],
        "entry_point": "agent.py",
        "requirements": "openai>=1.0\nrequests"
      }'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/api/deploy",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "agent_name": "payment-agent",
            "source_files": {
                "agent.py": "import requests\nimport openai\n..."
            },
            "system_prompt": "You are a payment processing assistant.",
            "tools_to_create": [
                {
                    "name": "stripe-api",
                    "description": "Stripe payments API",
                    "base_url": "https://api.stripe.com",
                    "auth_type": "APIKey",
                }
            ],
            "required_tools": ["stripe-api"],
            "llm_configs": [
                {"role": "chat", "provider": "openai", "model": "gpt-4o-mini"}
            ],
            "entry_point": "agent.py",
            "requirements": "openai>=1.0\nrequests",
        },
    )
    print(resp.json())
    ```

### Response (201 Created)

```json
{
  "agent": "payment-agent",
  "namespace": "agent-system",
  "tools_created": ["stripe-api"],
  "build_id": "build-a1b2c3",
  "image_uri": "registry.runagents.io/payment-agent:a1b2c3"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `agent` | string | Name of the created/updated agent |
| `namespace` | string | Namespace where the agent was deployed |
| `tools_created` | string[] | Names of tools that were created as part of this deploy |
| `build_id` | string | Build ID (present when source files triggered a server-side build) |
| `image_uri` | string | Container image URI (present when a build was triggered) |

### Example: Deploy with a pre-built image

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/deploy \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "agent_name": "my-agent",
        "image": "myregistry.io/my-agent:v1.2.0",
        "required_tools": ["echo-tool"],
        "llm_configs": [
          {"provider": "openai", "model": "gpt-4o-mini"}
        ]
      }'
    ```

### Response (201 Created)

```json
{
  "agent": "my-agent",
  "namespace": "agent-system",
  "tools_created": []
}
```

### Example: Multi-model deploy

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/deploy \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "agent_name": "rag-agent",
        "image": "myregistry.io/rag-agent:latest",
        "llm_configs": [
          {"role": "chat", "provider": "openai", "model": "gpt-4o"},
          {"role": "embedding", "provider": "openai", "model": "text-embedding-3-small"},
          {"role": "reranking", "provider": "anthropic", "model": "claude-3-haiku-20240307"}
        ],
        "required_tools": ["vector-db"]
      }'
    ```

The agent receives role-based environment variables:

| Environment Variable | Value |
|---------------------|-------|
| `LLM_MODEL` | `gpt-4o` |
| `LLM_PROVIDER` | `openai` |
| `LLM_MODEL_EMBEDDING` | `text-embedding-3-small` |
| `LLM_PROVIDER_EMBEDDING` | `openai` |
| `LLM_MODEL_RERANKING` | `claude-3-haiku-20240307` |
| `LLM_PROVIDER_RERANKING` | `anthropic` |

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `400` | `agent_name is required` | Missing required field |
| `400` | `either image or source_files is required` | Must provide one of `image` or `source_files` |
| `400` | `tool name and base_url are required` | Tool in `tools_to_create` missing required fields |
| `500` | `build failed: ...` | Server-side build failed |
| `500` | `failed to create tool "...": ...` | Tool creation failed |
| `500` | `failed to create agent: ...` | Agent creation failed |

---

## Seed Starter Kit

<span class="method-post">POST</span> <span class="endpoint">/api/starter-kit</span>

Creates built-in starter resources for first-time users. This is idempotent and safe to call multiple times.

Creates:

- **echo-tool** -- A built-in echo tool for testing (no external dependencies)
- **playground-llm** -- A playground model provider (OpenAI gpt-4o-mini)

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/starter-kit \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "status": "ok",
  "message": "Starter kit resources created"
}
```

!!! note
    Starter kit resources are labeled for demo purposes and should be replaced with production tools and model providers for real workloads.
