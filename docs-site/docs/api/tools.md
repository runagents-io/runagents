# Tools API

Register and manage external tools that your agents can access. Tools represent APIs and services that agents call during execution. RunAgents handles authentication, authorization, and traffic routing for each registered tool.

---

## List Tools

<span class="method-get">GET</span> <span class="endpoint">/api/tools</span>

Returns all registered tools.

=== "curl"

    ```bash
    curl https://api.runagents.io/api/tools \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
[
  {
    "name": "stripe-api",
    "namespace": "agent-system",
    "spec": {
      "description": "Stripe payments API",
      "connection": {
        "topology": "External",
        "baseUrl": "https://api.stripe.com",
        "port": 443,
        "scheme": "HTTPS",
        "authentication": {
          "type": "APIKey",
          "apiKeyConfig": {
            "in": "Header",
            "name": "Authorization",
            "valuePrefix": "Bearer ",
            "secretRef": {"name": "stripe-credentials"}
          }
        }
      },
      "governance": {
        "accessControl": {"mode": "Restricted"}
      }
    },
    "status": {
      "phase": "Available",
      "last_probe_time": "2026-02-23T10:30:00Z",
      "probe_latency_ms": 142
    }
  }
]
```

---

## Create a Tool

<span class="method-post">POST</span> <span class="endpoint">/api/tools</span>

Register a new tool. Idempotent -- creating a tool with an existing name updates it.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique tool name |
| `spec` | object | Yes | Tool specification (see [Tool Object Reference](#tool-object-reference)) |
| `credentials` | object | No | Credential values (the platform securely stores them for you) |

#### Credentials Object

| Field | Type | Description |
|-------|------|-------------|
| `client_id` | string | OAuth2 client ID |
| `client_secret` | string | OAuth2 client secret |
| `api_key` | string | API key value |

!!! tip
    When you provide `credentials`, RunAgents creates a secure credential store entry automatically and wires it into the tool's authentication config. You do not need to manage secrets separately.

### Example: Create a tool with OAuth2 authentication

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/tools \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "google-drive",
        "spec": {
          "description": "Google Drive file management",
          "connection": {
            "topology": "External",
            "baseUrl": "https://www.googleapis.com",
            "port": 443,
            "scheme": "HTTPS",
            "authentication": {
              "type": "OAuth2",
              "oauth2Config": {
                "authUrl": "https://accounts.google.com/o/oauth2/v2/auth",
                "tokenUrl": "https://oauth2.googleapis.com/token",
                "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
              }
            }
          },
          "governance": {
            "accessControl": {
              "mode": "Restricted",
              "requireApproval": false
            },
            "caching": {
              "enabled": true,
              "duration": "5m"
            }
          },
          "capabilities": [
            {
              "name": "list-files",
              "method": "GET",
              "path": "/drive/v3/files",
              "description": "List files in Google Drive"
            },
            {
              "name": "get-file",
              "method": "GET",
              "path": "/drive/v3/files/*",
              "description": "Get file metadata"
            }
          ],
          "riskTags": ["pii"]
        },
        "credentials": {
          "client_id": "123456789.apps.googleusercontent.com",
          "client_secret": "GOCSPX-..."
        }
      }'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/api/tools",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "name": "google-drive",
            "spec": {
                "description": "Google Drive file management",
                "connection": {
                    "topology": "External",
                    "baseUrl": "https://www.googleapis.com",
                    "port": 443,
                    "scheme": "HTTPS",
                    "authentication": {
                        "type": "OAuth2",
                        "oauth2Config": {
                            "authUrl": "https://accounts.google.com/o/oauth2/v2/auth",
                            "tokenUrl": "https://oauth2.googleapis.com/token",
                            "scopes": [
                                "https://www.googleapis.com/auth/drive.readonly"
                            ],
                        },
                    },
                },
                "governance": {
                    "accessControl": {"mode": "Restricted", "requireApproval": False},
                    "caching": {"enabled": True, "duration": "5m"},
                },
                "capabilities": [
                    {
                        "name": "list-files",
                        "method": "GET",
                        "path": "/drive/v3/files",
                        "description": "List files in Google Drive",
                    },
                    {
                        "name": "get-file",
                        "method": "GET",
                        "path": "/drive/v3/files/*",
                        "description": "Get file metadata",
                    },
                ],
                "riskTags": ["pii"],
            },
            "credentials": {
                "client_id": "123456789.apps.googleusercontent.com",
                "client_secret": "GOCSPX-...",
            },
        },
    )
    print(resp.json())
    ```

### Response (201 Created)

```json
{
  "name": "google-drive",
  "namespace": "agent-system",
  "spec": {
    "description": "Google Drive file management",
    "connection": {
      "topology": "External",
      "baseUrl": "https://www.googleapis.com",
      "port": 443,
      "scheme": "HTTPS",
      "authentication": {
        "type": "OAuth2",
        "oauth2Config": {
          "authUrl": "https://accounts.google.com/o/oauth2/v2/auth",
          "tokenUrl": "https://oauth2.googleapis.com/token",
          "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
          "credentialsSecretRef": {
            "name": "google-drive-credentials",
            "namespace": "agent-system"
          }
        }
      }
    },
    "governance": {
      "accessControl": {"mode": "Restricted", "requireApproval": false},
      "caching": {"enabled": true, "duration": "5m"}
    },
    "capabilities": [
      {"name": "list-files", "method": "GET", "path": "/drive/v3/files", "description": "List files in Google Drive"},
      {"name": "get-file", "method": "GET", "path": "/drive/v3/files/*", "description": "Get file metadata"}
    ],
    "riskTags": ["pii"]
  },
  "status": {
    "phase": "Pending"
  }
}
```

### Example: Create a tool with API key authentication

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/tools \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "stripe-api",
        "spec": {
          "description": "Stripe payments API",
          "connection": {
            "topology": "External",
            "baseUrl": "https://api.stripe.com",
            "port": 443,
            "scheme": "HTTPS",
            "authentication": {
              "type": "APIKey",
              "apiKeyConfig": {
                "in": "Header",
                "name": "Authorization",
                "valuePrefix": "Bearer "
              }
            }
          },
          "governance": {
            "accessControl": {"mode": "Restricted", "requireApproval": true},
            "approval": {
              "group": "platform-admins",
              "defaultDuration": "4h",
              "autoExpire": true
            }
          },
          "capabilities": [
            {"name": "list-charges", "method": "GET", "path": "/v1/charges", "description": "List charges"},
            {"name": "create-charge", "method": "POST", "path": "/v1/charges", "description": "Create a charge", "riskTags": ["financial", "destructive"]}
          ],
          "riskTags": ["financial"]
        },
        "credentials": {
          "api_key": "sk_live_..."
        }
      }'
    ```

---

## Get Tool Details

<span class="method-get">GET</span> <span class="endpoint">/api/tools/:name</span>

Retrieve details for a specific tool.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Tool name |

=== "curl"

    ```bash
    curl https://api.runagents.io/api/tools/stripe-api \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

Returns the full tool object (same format as the create response).

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `tool "stripe-api" not found` | Tool does not exist |

---

## Delete a Tool

<span class="method-delete">DELETE</span> <span class="endpoint">/api/tools/:name</span>

Delete a registered tool.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Tool name |

=== "curl"

    ```bash
    curl -X DELETE https://api.runagents.io/api/tools/stripe-api \
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
| `404` | `tool "stripe-api" not found` | Tool does not exist |

---

## Probe a URL

<span class="method-post">POST</span> <span class="endpoint">/api/tools/probe</span>

Test connectivity to a URL before registering it as a tool. Returns reachability status and latency.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL to probe |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/tools/probe \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"url": "https://api.stripe.com"}'
    ```

### Response (200 OK)

```json
{
  "reachable": true,
  "status_code": 401,
  "latency_ms": 142
}
```

!!! info
    A `401` or `403` status code still means the endpoint is **reachable** -- it just requires authentication. Only `5xx` responses and network errors indicate an unreachable host.

---

## Test a Registered Tool

<span class="method-post">POST</span> <span class="endpoint">/api/tools/:name/test</span>

Probe a registered tool's base URL and update its status with the result.

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/tools/stripe-api/test \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "reachable": true,
  "status_code": 401,
  "latency_ms": 156
}
```

---

## Tool Object Reference

### Connection

| Field | Type | Description |
|-------|------|-------------|
| `topology` | string | `External` (public API) or `Internal` (same-network service) |
| `baseUrl` | string | Tool endpoint URL |
| `port` | integer | Target port (default: `443`) |
| `scheme` | string | Protocol: `HTTPS` or `HTTP` |
| `authentication` | object | Authentication configuration |
| `tls` | object | TLS settings (optional) |

### Authentication Types

#### None

No authentication. The platform passes requests through without injecting credentials.

```json
{"type": "None"}
```

#### APIKey

Injects an API key as a header or query parameter.

```json
{
  "type": "APIKey",
  "apiKeyConfig": {
    "in": "Header",
    "name": "Authorization",
    "valuePrefix": "Bearer ",
    "secretRef": {"name": "my-api-key-secret"}
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `in` | string | Where to inject: `Header` or `Query` |
| `name` | string | Header or query parameter name |
| `valuePrefix` | string | Prefix prepended to the key value (e.g., `"Bearer "`) |
| `secretRef` | object | Reference to the stored credentials |

#### OAuth2

Manages OAuth2 token lifecycle including refresh and user consent flows.

```json
{
  "type": "OAuth2",
  "oauth2Config": {
    "authUrl": "https://accounts.google.com/o/oauth2/v2/auth",
    "tokenUrl": "https://oauth2.googleapis.com/token",
    "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
    "credentialsSecretRef": {"name": "google-credentials"}
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `authUrl` | string | Authorization endpoint (triggers user consent flow) |
| `tokenUrl` | string | Token endpoint for exchanging codes and refreshing tokens |
| `scopes` | string[] | OAuth2 scopes to request |
| `authParams` | object | Additional authorization parameters (key-value pairs) |
| `credentialsSecretRef` | object | Reference to stored client credentials |

### Governance

| Field | Type | Description |
|-------|------|-------------|
| `accessControl.mode` | string | Access mode (see below) |
| `accessControl.requireApproval` | boolean | Whether denied access triggers the JIT approval flow |
| `approval.group` | string | Admin group that reviews access requests |
| `approval.defaultDuration` | string | Default access window (e.g., `"4h"`) |
| `approval.autoExpire` | boolean | Automatically clean up expired access |
| `caching.enabled` | boolean | Enable response caching |
| `caching.duration` | string | Cache TTL (e.g., `"5m"`) |

### Access Modes

| Mode | Behavior |
|------|----------|
| `Open` | All agents are automatically granted access |
| `Restricted` | Access requires explicit policy binding. Agents must be authorized before calling the tool |
| `Critical` | Same as Restricted, plus requires admin approval for each access grant |

### Capabilities

Capabilities define the specific operations a tool exposes. When capabilities are defined, RunAgents enforces that agent requests match at least one capability (method + path prefix). If no capabilities are defined, all requests are allowed through.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Capability identifier |
| `method` | string | HTTP method (`GET`, `POST`, `PUT`, `DELETE`, etc.) |
| `path` | string | URL path pattern (supports `*` wildcard) |
| `description` | string | Human-readable description |
| `riskTags` | string[] | Risk categories for this specific capability |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `phase` | string | `Pending`, `Available`, or `Unreachable` |
| `message` | string | Status detail (populated on errors) |
| `last_probe_time` | string | ISO 8601 timestamp of last connectivity check |
| `probe_latency_ms` | integer | Round-trip latency of last probe in milliseconds |
