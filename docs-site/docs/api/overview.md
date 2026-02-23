# API Overview

The RunAgents API lets you programmatically deploy agents, register tools, manage model providers, orchestrate runs, and handle approvals. Everything you can do in the console is available via the API.

## Base URL

All API requests are made to:

```
https://api.runagents.io
```

## Authentication

Every API request must include an API key in the `Authorization` header:

```
Authorization: Bearer <api-key>
```

Obtain your API key from **Settings** in the [RunAgents Console](https://console.runagents.io).

=== "curl"

    ```bash
    curl https://api.runagents.io/api/agents \
      -H "Authorization: Bearer ra_live_abc123..."
    ```

=== "Python"

    ```python
    import requests

    headers = {"Authorization": "Bearer ra_live_abc123..."}
    resp = requests.get("https://api.runagents.io/api/agents", headers=headers)
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

## Interactive API Docs

!!! info "Coming soon"
    Interactive Swagger/OpenAPI documentation is in progress. Subscribe for updates at [try@runagents.io](mailto:try@runagents.io).

## API Endpoints at a Glance

| Endpoint Group | Description | Documentation |
|----------------|-------------|---------------|
| `/api/deploy` | Deploy agents programmatically | [Deploy API](deploy.md) |
| `/api/agents` | List, get, and delete agents | [Agents API](agents.md) |
| `/api/tools` | Register and manage tools | [Tools API](tools.md) |
| `/api/model-providers` | Configure LLM providers | [Model Providers API](model-providers.md) |
| `/api/identity-providers` | Set up authentication providers | [Identity Providers API](identity-providers.md) |
| `/runs` | Agent run lifecycle and events | [Runs API](runs.md) |
| `/governance/requests` | JIT access request approvals | [Approvals API](approvals.md) |
| `/v1/chat/completions` | OpenAI-compatible LLM gateway | [Model Providers & LLM Gateway](model-providers.md) |
| `/analyze` | Code analysis and detection | [Ingestion API](ingestion.md) |
| `/api/builds` | Container image builds | [Build API](build.md) |
