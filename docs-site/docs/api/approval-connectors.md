# Approval Connectors API

Manage approval delivery connectors, workspace defaults, and connector activity.

Approval connectors let RunAgents route approval-required events into external systems such as Slack, Microsoft Teams, Jira, PagerDuty, or custom webhooks while still falling back to the console when needed.

---

## List Approval Connectors

<span class="method-get">GET</span> <span class="endpoint">/api/settings/approval-connectors</span>

Returns approval connectors configured in the current workspace.

=== "curl"

    ```bash
    curl https://api.runagents.io/api/settings/approval-connectors \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "X-Workspace-Namespace: default"
    ```

### Response (200 OK)

```json
[
  {
    "id": "ac_01hxyz...",
    "name": "secops-slack",
    "type": "slack",
    "endpoint": "C0123456789",
    "headers": {
      "X-Slack-Bot-Token": "xoxb-..."
    },
    "enabled": true,
    "timeout_seconds": 15,
    "slack_security_mode": "compat",
    "created_at": "2026-04-09T15:10:00Z",
    "updated_at": "2026-04-09T15:10:00Z"
  }
]
```

---

## Create Approval Connector

<span class="method-post">POST</span> <span class="endpoint">/api/settings/approval-connectors</span>

Create a workspace-scoped approval connector.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Friendly connector name |
| `type` | string | No | Connector type: `webhook`, `slack`, `teams`, `jira`, or `pagerduty`. Defaults to `webhook` |
| `endpoint` | string | Yes | Target endpoint, channel ID, webhook URL, or connector-specific target |
| `headers` | object | No | Connector-specific headers or credentials |
| `enabled` | boolean | No | Whether the connector is enabled. Defaults to `true` |
| `timeout_seconds` | integer | No | Connector timeout in seconds. Allowed range: `1`-`120` |
| `slack_security_mode` | string | No | Slack security mode: `compat` or `strict` |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/settings/approval-connectors \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "X-Workspace-Namespace: default" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "secops-slack",
        "type": "slack",
        "endpoint": "C0123456789",
        "headers": {
          "X-Slack-Bot-Token": "xoxb-..."
        },
        "timeout_seconds": 15,
        "slack_security_mode": "compat"
      }'
    ```

### Response (201 Created)

Returns the created connector.

---

## Get Approval Connector

<span class="method-get">GET</span> <span class="endpoint">/api/settings/approval-connectors/:id</span>

Returns a single connector.

---

## Update Approval Connector

<span class="method-patch">PATCH</span> <span class="endpoint">/api/settings/approval-connectors/:id</span>

Update one or more mutable connector fields.

### Request Body

All fields are optional. Include only the fields you want to change.

```json
{
  "enabled": false,
  "timeout_seconds": 20
}
```

### Response (200 OK)

Returns the updated connector.

---

## Delete Approval Connector

<span class="method-delete">DELETE</span> <span class="endpoint">/api/settings/approval-connectors/:id</span>

Deletes the named connector.

### Response (200 OK)

```json
{
  "status": "deleted"
}
```

---

## Test Approval Connector

<span class="method-post">POST</span> <span class="endpoint">/api/settings/approval-connectors/test</span>

Validates connector configuration and attempts a live delivery test when possible.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | No | Connector type |
| `endpoint` | string | Yes | Target endpoint or channel |
| `headers` | object | No | Connector-specific headers or credentials |
| `timeout_seconds` | integer | No | Timeout in seconds |
| `slack_security_mode` | string | No | Slack security mode |

### Response (200 OK)

```json
{
  "status": "healthy",
  "connector_type": "webhook",
  "endpoint": "https://approvals.example.com/hook",
  "checks": [
    {
      "id": "config",
      "label": "Configuration",
      "status": "passed",
      "message": "Connector configuration is valid"
    },
    {
      "id": "credentials",
      "label": "Credentials",
      "status": "passed",
      "message": "Required credentials are present"
    },
    {
      "id": "connectivity",
      "label": "Connectivity",
      "status": "passed",
      "message": "Connector endpoint accepted the test request",
      "duration_ms": 148
    }
  ]
}
```

A response can still be `200 OK` with `status: "unhealthy"` when the test ran successfully but one or more checks failed.

---

## Get Connector Defaults

<span class="method-get">GET</span> <span class="endpoint">/api/settings/approval-connectors/defaults</span>

Returns workspace defaults used when an approval policy omits explicit connector delivery settings.

### Response (200 OK)

```json
{
  "default_delivery_mode": "first_success",
  "default_fallback_to_ui": true,
  "default_timeout_seconds": 10,
  "min_timeout_seconds": 1,
  "max_timeout_seconds": 120
}
```

---

## Update Connector Defaults

<span class="method-put">PUT</span> <span class="endpoint">/api/settings/approval-connectors/defaults</span>

Update one or more workspace defaults.

### Request Body

```json
{
  "default_delivery_mode": "all",
  "default_fallback_to_ui": true,
  "default_timeout_seconds": 20
}
```

### Response (200 OK)

Returns the updated defaults.

---

## Get Connector Activity

<span class="method-get">GET</span> <span class="endpoint">/api/settings/approval-connectors/activity</span>

Returns recent approval connector activity for the current workspace.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Maximum number of activity records to return |

### Response (200 OK)

```json
[
  {
    "id": "aca_01hxyz...",
    "timestamp": "2026-04-09T15:18:31Z",
    "event": "dispatch_succeeded",
    "connector_id": "ac_01hxyz...",
    "connector_name": "secops-slack",
    "request_id": "req_123",
    "decision": "approved",
    "status_code": 200,
    "duration_ms": 148,
    "message": "Connector delivery succeeded"
  }
]
```

---

## Supported Connector Types

RunAgents currently supports these connector types:

- `webhook`
- `slack`
- `teams`
- `jira`
- `pagerduty`

Connector-specific validation applies. For example:

- Slack strict mode requires an `X-Slack-Signing-Secret` header
- PagerDuty requires a routing key header
- Webhook connectors expect an HTTPS endpoint

---

## Errors

| Status | Meaning |
|--------|---------|
| `400` | Invalid connector configuration or unsupported field values |
| `404` | Connector not found |
| `409` | Conflicting workspace state |
| `500` | Internal error while loading or persisting connector state |

---

## Related

- [Approvals API](approvals.md)
- [Policies API](policies.md)
- [Platform Approvals Guide](../platform/approvals.md)
