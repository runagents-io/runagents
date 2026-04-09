# Catalog API

Discover production-shaped agent blueprints from the RunAgents catalog.

The catalog powers workflows such as:

- listing available starter agents
- inspecting a catalog agent before deploy
- selecting a specific published version
- deploying a blueprint such as the Google Workspace assistant through your own automation

---

## List Catalog Agents

<span class="method-get">GET</span> <span class="endpoint">/api/catalog</span>

Returns paginated catalog entries.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Full-text search across id, name, summary, tags, and integrations |
| `category` | string or csv | Filter by category |
| `tag` | string or csv | Filter by tag |
| `integration` | string or csv | Filter by required integration |
| `governance` | string or csv | Filter by governance trait |
| `page` | int | Page number, default `1` |
| `page_size` | int | Page size, default `24`, max `100` |

=== "curl"

    ```bash
    curl "https://api.runagents.io/api/catalog?search=google&integration=calendar" \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "generated_at": "2026-04-09T20:00:00Z",
  "items": [
    {
      "id": "google-workspace-assistant-agent",
      "name": "Google Workspace Assistant",
      "summary": "Acts like a Google-native work assistant across Gmail, Calendar, Drive, Docs, Sheets, Tasks, and Keep.",
      "category": "Enterprise Productivity",
      "tags": ["Google Workspace", "Productivity", "Gmail"],
      "latest_version": "1.2.0",
      "required_integrations": ["email", "calendar", "drive", "docs", "sheets", "tasks", "keep"],
      "governance_traits": ["identity-aware", "approval-ready", "audit-ready"],
      "complexity": "high"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 24
}
```

---

## Get Latest Catalog Manifest

<span class="method-get">GET</span> <span class="endpoint">/api/catalog/:id</span>

Returns the latest manifest for a catalog agent, or a specific version when `version` is supplied.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Catalog agent id |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `version` | string | Optional explicit version |

=== "curl"

    ```bash
    curl "https://api.runagents.io/api/catalog/google-workspace-assistant-agent" \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "id": "google-workspace-assistant-agent",
  "version": "1.2.0",
  "name": "Google Workspace Assistant",
  "summary": "Acts like a Google-native work assistant across Gmail, Calendar, Drive, Docs, Sheets, Tasks, and Keep.",
  "defaultModel": "gpt-4.1",
  "requiredIntegrations": ["email", "calendar", "drive", "docs", "sheets", "tasks", "keep"],
  "governanceTraits": ["identity-aware", "approval-ready", "audit-ready"],
  "deploymentTemplate": {
    "agentName": "google-workspace-assistant-agent",
    "systemPrompt": "You are a Google Workspace assistant.",
    "requiredTools": ["email", "calendar", "drive", "docs", "sheets", "tasks", "keep"],
    "policies": [],
    "identityProvider": "corp-sso",
    "sourceType": "python_source",
    "sourceFiles": {
      "src/agent.py": "..."
    }
  }
}
```

---

## List Catalog Versions

<span class="method-get">GET</span> <span class="endpoint">/api/catalog/:id/versions</span>

Returns the published versions for a catalog agent in descending semantic-version order.

=== "curl"

    ```bash
    curl "https://api.runagents.io/api/catalog/google-workspace-assistant-agent/versions" \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "agent_id": "google-workspace-assistant-agent",
  "versions": [
    {
      "version": "1.2.0",
      "published_at": "2026-04-06T22:00:00Z",
      "summary": "Acts like a Google-native work assistant across Gmail, Calendar, Drive, Docs, Sheets, Tasks, and Keep.",
      "changelog": "Added an explicit Google Calendar event creation tool for clear scheduling requests while keeping write actions policy-controlled."
    }
  ]
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `catalog entry not found` | Unknown catalog id or version |
| `400` | `invalid catalog path` | Malformed path |
