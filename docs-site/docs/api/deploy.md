# Deploy API

Deploy or update agents programmatically.

`POST /api/deploy` supports both image-based deploys and source-file deploys with optional server-side build.

---

## Deploy An Agent

<span class="method-post">POST</span> <span class="endpoint">/api/deploy</span>

Idempotent by `agent_name` within namespace.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_name` | string | Yes | Agent name |
| `namespace` | string | No | Workspace namespace (must match workspace header) |
| `image` | string | No* | Pre-built image URI |
| `source_files` | object | No* | Map of filename to file contents |
| `artifact_id` | string | No | Existing workflow artifact to deploy |
| `draft_id` | string | No | Existing deploy draft to hydrate from |
| `system_prompt` | string | No | Agent system prompt |
| `required_tools` | string[] | No | Registered tool names required by the agent |
| `tool_url_mappings` | object | No | Rewrite map of detected URL -> tool name |
| `tools_to_create` | object[] | No | Tools to create as part of deploy |
| `llm_configs` | object[] | No | Role-based model configs |
| `env` | object[] | No | Extra env vars |
| `requirements` | string | No | Requirements text for build |
| `entry_point` | string | No | Source entry point |
| `framework` | string | No | Framework hint (e.g., `langchain`) |
| `identity_provider` | string | No | Agent ingress identity provider |
| `policies` | string[] | No | Policy names to bind to this agent |

`*` Provide at least one of `image`, `source_files`, or `artifact_id`.

### Tool Object (`tools_to_create`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool name |
| `base_url` | string | Yes | Tool base URL |
| `description` | string | No | Tool description |
| `auth_type` | string | No | `None`, `APIKey`, `OAuth2` |
| `port` | integer | No | Tool port |
| `scheme` | string | No | `HTTP` or `HTTPS` |

### Response (201)

```json
{
  "agent": "payment-agent",
  "namespace": "default",
  "tools_created": ["stripe-api"],
  "build_id": "build-a1b2c3",
  "image_uri": "registry.example.com/payment-agent:a1b2c3",
  "execution_mode": "FAST_OVERLAY",
  "build_required": true,
  "build_profile": "fast_overlay",
  "decision_reason": "Detected framework runtime overlay path"
}
```

| Field | Description |
|---|---|
| `tools_created` | Tools created during this request |
| `build_id`, `image_uri` | Present when build path is used |
| `execution_mode`, `build_required`, `build_profile`, `decision_reason` | Deployment decision metadata |

---

## Example: Source Deploy With Policy Bindings

```bash
curl -X POST https://api.runagents.io/api/deploy \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "billing-agent",
    "source_files": {
      "agent.py": "print(\"hello\")"
    },
    "required_tools": ["stripe-api"],
    "llm_configs": [{"provider": "openai", "model": "gpt-4o-mini", "role": "chat"}],
    "policies": ["billing-stripe-policy"],
    "entry_point": "agent.py",
    "requirements": "runagents>=1.2.1\n"
  }'
```

---

## Example: Image Deploy

```bash
curl -X POST https://api.runagents.io/api/deploy \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "my-agent",
    "image": "ghcr.io/acme/my-agent:1.2.0",
    "required_tools": ["echo-tool"],
    "policies": ["echo-read-policy"],
    "llm_configs": [{"provider": "openai", "model": "gpt-4o-mini"}]
  }'
```

---

## Common Errors

| Status | Error |
|--------|-------|
| `400` | Missing required fields (e.g. `agent_name`) |
| `400` | Namespace mismatch with workspace header |
| `400` | No valid deploy source (`image`, `source_files`, `artifact_id`) |
| `500` | Tool/agent/build creation failed |

---

## Starter Kit Endpoint

<span class="method-post">POST</span> <span class="endpoint">/api/starter-kit</span>

Seeds demo resources in the workspace namespace:

- `echo-tool`
- `playground-llm`

### Response (201)

```json
{
  "tool_created": "echo-tool",
  "model_provider_created": "playground-llm"
}
```
