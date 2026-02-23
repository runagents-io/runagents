# Approvals API

Manage just-in-time (JIT) access requests for restricted tools. When an agent attempts to call a tool with `requireApproval: true` and no existing access policy, the platform creates an access request that must be approved by an admin before the agent can proceed.

---

## Create Access Request

<span class="method-post">POST</span> <span class="endpoint">/governance/requests</span>

Create a new access request. This endpoint is idempotent -- if a pending request already exists for the same subject and tool, the existing request is returned.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | User or service identity requesting access |
| `tool_id` | string | Yes | Name of the tool being requested |
| `agent_id` | string | No | Agent making the request |
| `duration` | string | No | Requested access duration (e.g., `"4h"`, `"1d"`) |
| `run_id` | string | No | Associated run ID (enables automatic run pausing) |
| `capability` | string | No | Specific tool capability being requested |
| `payload_hash` | string | No | SHA-256 hash of the action payload for integrity |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/governance/requests \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "subject": "payment-agent-sa",
        "tool_id": "stripe-api",
        "agent_id": "payment-agent",
        "duration": "4h",
        "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "capability": "create-charge",
        "payload_hash": "sha256:abc123"
      }'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/governance/requests",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "subject": "payment-agent-sa",
            "tool_id": "stripe-api",
            "agent_id": "payment-agent",
            "duration": "4h",
            "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        },
    )
    print(resp.json())
    ```

### Response (201 Created)

```json
{
  "id": "req-a1b2c3d4-e5f6-7890",
  "status": "PENDING",
  "action_id": "act-x1y2z3"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Access request ID |
| `status` | string | Initial status: `PENDING` |
| `action_id` | string | Blocked action ID (present when `run_id` was provided) |

!!! info "Run correlation"
    When `run_id` is provided, the platform automatically:

    1. Creates a blocked action for the tool call
    2. Pauses the run (status changes to `PAUSED_APPROVAL`)
    3. Appends an `APPROVAL_REQUIRED` event to the run's audit log

    This enables the console to display the paused run with approval context.

### Idempotency

If a `PENDING` request already exists for the same `subject` and `tool_id`, the existing request is returned with a `200 OK` instead of creating a duplicate.

---

## List Access Requests

<span class="method-get">GET</span> <span class="endpoint">/governance/requests</span>

List access requests. By default, returns requests in `PENDING` status.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED` |

=== "curl"

    ```bash
    # List pending requests
    curl https://api.runagents.io/governance/requests \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"

    # List approved requests
    curl "https://api.runagents.io/governance/requests?status=APPROVED" \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
[
  {
    "id": "req-a1b2c3d4-e5f6-7890",
    "subject": "payment-agent-sa",
    "agent_id": "payment-agent",
    "tool_id": "stripe-api",
    "status": "PENDING",
    "duration": "4h",
    "created_at": "2026-02-23T10:00:00Z",
    "updated_at": "2026-02-23T10:00:00Z"
  }
]
```

---

## Get Access Request Details

<span class="method-get">GET</span> <span class="endpoint">/governance/requests/:id</span>

Retrieve details for a specific access request.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Access request ID |

=== "curl"

    ```bash
    curl https://api.runagents.io/governance/requests/req-a1b2c3d4-e5f6-7890 \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "id": "req-a1b2c3d4-e5f6-7890",
  "subject": "payment-agent-sa",
  "agent_id": "payment-agent",
  "tool_id": "stripe-api",
  "status": "PENDING",
  "duration": "4h",
  "created_at": "2026-02-23T10:00:00Z",
  "updated_at": "2026-02-23T10:00:00Z"
}
```

---

## Approve Access Request

<span class="method-post">POST</span> <span class="endpoint">/governance/requests/:id/approve</span>

Approve a pending access request. This creates a time-limited access policy that allows the agent to call the tool.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Access request ID |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/governance/requests/req-a1b2c3d4-e5f6-7890/approve \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{}'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/governance/requests/req-a1b2c3d4-e5f6-7890/approve",
        headers={"Authorization": f"Bearer {api_key}"},
        json={},
    )
    print(resp.json())
    ```

### Response (200 OK)

```json
{
  "id": "req-a1b2c3d4-e5f6-7890",
  "subject": "payment-agent-sa",
  "agent_id": "payment-agent",
  "tool_id": "stripe-api",
  "status": "APPROVED",
  "duration": "4h",
  "approver_id": "admin@example.com",
  "expires_at": "2026-02-23T14:00:00Z",
  "created_at": "2026-02-23T10:00:00Z",
  "updated_at": "2026-02-23T10:05:00Z"
}
```

### What happens on approval

1. A **time-limited access policy** is created granting the agent access to the tool
2. The policy expires after the requested duration (default: 4 hours)
3. If the request was associated with a run, the corresponding blocked action is marked as `APPROVED`
4. The platform's resume worker automatically detects approved actions and resumes paused runs

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `request not found` | Access request does not exist |
| `409` | `request is not pending` | Request has already been approved, rejected, or expired |

---

## Reject Access Request

<span class="method-post">POST</span> <span class="endpoint">/governance/requests/:id/reject</span>

Reject a pending access request.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Access request ID |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/governance/requests/req-a1b2c3d4-e5f6-7890/reject \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"reason": "Not authorized for production Stripe access"}'
    ```

### Request Body (optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | No | Reason for rejection |

### Response (200 OK)

```json
{
  "id": "req-a1b2c3d4-e5f6-7890",
  "subject": "payment-agent-sa",
  "tool_id": "stripe-api",
  "status": "REJECTED",
  "reason": "Not authorized for production Stripe access",
  "updated_at": "2026-02-23T10:05:00Z"
}
```

---

## Access Request Lifecycle

```
PENDING --> APPROVED --> (auto) EXPIRED
PENDING --> REJECTED
```

| Status | Description |
|--------|-------------|
| `PENDING` | Awaiting admin review |
| `APPROVED` | Access granted with a time-limited policy |
| `REJECTED` | Access denied by admin |
| `EXPIRED` | Time-limited policy has expired (automatic) |

### Automatic Expiry

When an access request is approved, the platform creates an access policy with a TTL (default: 4 hours, configurable per tool via `governance.approval.defaultDuration`). When the TTL expires:

1. The access policy is automatically removed by the garbage collector
2. The access request status transitions to `EXPIRED`
3. The agent can no longer call the tool until a new request is approved

!!! tip "Configuring approval TTL"
    Set the default approval duration per tool in the tool's governance configuration:

    ```json
    {
      "governance": {
        "approval": {
          "defaultDuration": "8h",
          "autoExpire": true
        }
      }
    }
    ```

---

## Access Request Object Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique request ID |
| `subject` | string | Identity requesting access |
| `agent_id` | string | Agent making the request |
| `tool_id` | string | Target tool |
| `status` | string | Current status |
| `duration` | string | Requested access duration |
| `reason` | string | Rejection reason (when rejected) |
| `approver_id` | string | Who approved the request |
| `expires_at` | string | ISO 8601 expiration timestamp (when approved) |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |
