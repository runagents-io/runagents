# Policies API

Manage policy rules and approval routing for deployed agents.

Policies are the core governance object in RunAgents. They determine whether tool calls are:

- allowed
- denied
- routed into approval

---

## List Policies

<span class="method-get">GET</span> <span class="endpoint">/api/policies</span>

Returns policies in the current workspace, including bound-agent usage when available.

=== "curl"

    ```bash
    curl https://api.runagents.io/api/policies \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
[
  {
    "name": "workspace-write-approval",
    "namespace": "default",
    "spec": {
      "policies": [
        {
          "permission": "allow",
          "operations": ["GET"],
          "resource": "https://www.googleapis.com/*"
        },
        {
          "permission": "approval_required",
          "operations": ["POST", "PUT", "PATCH", "DELETE"],
          "resource": "https://www.googleapis.com/*"
        }
      ],
      "approvals": [
        {
          "name": "workspace-writes",
          "approvers": {
            "groups": ["self-approvers"]
          },
          "defaultDuration": "4h"
        }
      ]
    },
    "status": {
      "ready": true,
      "message": ""
    },
    "used_by": [
      {
        "name": "google-workspace-assistant-agent",
        "namespace": "default"
      }
    ]
  }
]
```

---

## Create Policy

<span class="method-post">POST</span> <span class="endpoint">/api/policies</span>

Create a policy from structured rules.

### Request Body

```json
{
  "name": "workspace-write-approval",
  "spec": {
    "policies": [
      {
        "permission": "allow",
        "operations": ["GET"],
        "resource": "https://www.googleapis.com/*"
      },
      {
        "permission": "approval_required",
        "operations": ["POST", "PUT", "PATCH", "DELETE"],
        "resource": "https://www.googleapis.com/*"
      }
    ],
    "approvals": [
      {
        "name": "workspace-writes",
        "toolIds": ["calendar"],
        "approvers": {
          "groups": ["self-approvers"]
        },
        "defaultDuration": "4h",
        "delivery": {
          "connectors": ["slack-finance"],
          "mode": "first_success",
          "fallbackToUI": true
        }
      }
    ]
  }
}
```

---

## Get Policy

<span class="method-get">GET</span> <span class="endpoint">/api/policies/:name</span>

Returns a single policy with usage metadata.

---

## Update Policy

<span class="method-put">PUT</span> <span class="endpoint">/api/policies/:name</span>

Replace the policy spec for an existing policy.

The request body matches `POST /api/policies`.

---

## Delete Policy

<span class="method-delete">DELETE</span> <span class="endpoint">/api/policies/:name</span>

Deletes the named policy.

### Response (200 OK)

```json
{
  "status": "deleted"
}
```

---

## Translate Natural Language to Policy Rules

<span class="method-post">POST</span> <span class="endpoint">/api/policies/translate</span>

Translate a natural-language description into structured policy rules.

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/policies/translate \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"text":"Allow Google Workspace reads and require approval for writes"}'
    ```

### Response (200 OK)

```json
{
  "rules": [
    {
      "permission": "allow",
      "operations": ["GET"]
    },
    {
      "permission": "approval_required",
      "operations": ["POST", "PUT"]
    }
  ]
}
```
