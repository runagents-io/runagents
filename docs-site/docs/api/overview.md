# API Overview

The RunAgents API lets you programmatically deploy agents, register tools, manage model providers, validate and apply action plans, orchestrate runs, and handle approvals.

## Base URL

RunAgents API clients use the URL they receive for their trial, company, or
workspace.

=== "Trial"

    ```text
    https://1406e38143ac0e57.try.runagents.io/api/v1
    ```

=== "Company default workspace"

    ```text
    https://acme.runagents.io/api/v1
    ```

=== "Company workspace"

    ```text
    https://acme.runagents.io/api/v1/workspaces/revops
    ```

The base URL carries tenant and workspace context. Kubernetes namespaces remain
internal to RunAgents.

## Authentication

Every API request should include a bearer token:

```http
Authorization: Bearer <token>
```

Tokens identify the caller and authorize access to the tenant/workspace in the
base URL. Tokens may be personal, service, or workspace-bound depending on how
they are created.

You can create and rotate workspace API keys from **Settings** in the [RunAgents Console](https://console.runagents.io) or programmatically through the auth endpoints documented in the canonical OpenAPI contract.

=== "curl"

    ```bash
    curl https://acme.runagents.io/api/v1/workspaces/revops/agents \
      -H "Authorization: Bearer ra_ws_abc123..."
    ```

=== "Python"

    ```python
    import requests

    headers = {"Authorization": "Bearer ra_ws_abc123..."}
    resp = requests.get(
        "https://acme.runagents.io/api/v1/workspaces/revops/agents",
        headers=headers,
    )
    ```

## Content Type

All request and response bodies use JSON:

```
Content-Type: application/json
```

## Error Format

Errors return a JSON object with an `error` field and an appropriate HTTP status code:

```json
{
  "error": "agent_name is required"
}
```

### Standard Error Codes

| Status Code | Meaning |
|-------------|---------|
| `400` | Bad Request -- invalid or missing parameters |
| `401` | Unauthorized -- missing or invalid API key |
| `403` | Forbidden -- insufficient permissions or approval required |
| `404` | Not Found -- resource does not exist |
| `405` | Method Not Allowed -- wrong HTTP method for this endpoint |
| `409` | Conflict -- state conflict (e.g., invalid status transition, payload hash mismatch) |
| `500` | Internal Server Error -- something went wrong on our end |

## Rate Limits

API requests are subject to rate limits. Current limits are configurable per account. If you exceed your rate limit, the API returns `429 Too Many Requests` with a `Retry-After` header.

!!! tip "Need higher limits?"
    Contact us at [try@runagents.io](mailto:try@runagents.io) to discuss your use case.

## Pagination

List endpoints currently return all resources in a single response. Pagination will be introduced in a future API version for endpoints with large result sets.

## Special Headers

RunAgents uses several special headers for identity propagation and run correlation:

| Header | Description | Set by |
|--------|-------------|--------|
| `X-End-User-ID` | Propagates the end-user identity from client through agent to tool | Platform (from JWT claim) |
| `X-Run-ID` | Correlates a tool call back to a specific agent run | Agent SDK |
| `X-Payload-Hash` | SHA-256 hash of the action payload for integrity verification during approvals | Agent SDK |

These headers are primarily used by the agent runtime and SDK. You do not need to set them for standard API calls.

## API Versioning

The RunAgents API is currently in **v1alpha**. While we aim for backward compatibility, breaking changes may occur before the stable v1 release.

Stable, versioned APIs (e.g., `/v1/...`) are planned for general availability. Subscribe for updates to be notified when versioned endpoints are available.

## OpenAPI Contract

The canonical machine-readable contract for the private programmatic API is now
available:

- [Full OpenAPI contract (`openapi.yaml`)](openapi.yaml)
- [Focused action plans fragment (`action-plans-openapi.yaml`)](action-plans-openapi.yaml)

Use the full contract as the source for generated SDK, CLI, and assistant
artifacts. The action plans fragment is kept as a focused reference for the
deterministic validate/apply flow.

## API Endpoints at a Glance

| Endpoint Group | Description | Documentation |
|----------------|-------------|---------------|
| `/deploy` | Deploy agents programmatically | [Deploy API](deploy.md) |
| `/actions/*` | Validate and apply deterministic action plans | [Action Plans API](actions.md) |
| `/agents` | List, get, delete, invoke, and configure agents | [Agents API](agents.md) |
| `/agents/{agentName}/config` | Configure model mappings, budgets, tools, policies, and identity | Full OpenAPI contract |
| `/tools` | Register and manage tools | [Tools API](tools.md) |
| `/model-providers` | Configure LLM providers | [Model Providers API](model-providers.md) |
| `/model-spend` | View model spend, budget warnings, and top model usage | Full OpenAPI contract |
| `/identity-providers` | Set up authentication providers | [Identity Providers API](identity-providers.md) |
| `/runs` | Agent run lifecycle and events | [Runs API](runs.md) |
| `/approvals/requests` | JIT access request approvals | [Approvals API](approvals.md) |
| `/chat/completions` | OpenAI-compatible LLM gateway | [Model Providers & LLM Gateway](model-providers.md) |
| `/analyze` | Code analysis and detection | [Ingestion API](ingestion.md) |
| `/builds` | Container image builds | [Build API](build.md) |
