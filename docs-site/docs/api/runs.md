# Runs API

Track agent execution with runs, events, and blocked actions. A run represents a single agent conversation or task execution. Events provide an ordered audit log. Blocked actions represent tool calls that require approval before the agent can proceed.

---

## Create a Run

<span class="method-post">POST</span> <span class="endpoint">/runs</span>

Start tracking a new agent run.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | string | Yes | Name of the agent |
| `user_id` | string | Yes | ID of the user who triggered the run |
| `conversation_id` | string | No | Conversation or session ID for grouping related runs |
| `namespace` | string | No | Agent namespace |
| `invoke_url` | string | No | Custom invoke endpoint URL. Auto-derived if not set |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/runs \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "agent_id": "payment-agent",
        "user_id": "user@example.com",
        "conversation_id": "conv-abc123",
        "namespace": "agent-system"
      }'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/runs",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "agent_id": "payment-agent",
            "user_id": "user@example.com",
            "conversation_id": "conv-abc123",
            "namespace": "agent-system",
        },
    )
    run = resp.json()
    print(f"Run ID: {run['id']}")
    ```

### Response (201 Created)

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "conversation_id": "conv-abc123",
  "agent_id": "payment-agent",
  "namespace": "agent-system",
  "user_id": "user@example.com",
  "status": "RUNNING",
  "created_at": "2026-02-23T10:00:00Z",
  "updated_at": "2026-02-23T10:00:00Z"
}
```

---

## List Runs

<span class="method-get">GET</span> <span class="endpoint">/runs</span>

List runs with optional filters. Without filters, returns all runs in `RUNNING` status.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Filter by agent name |
| `status` | string | Filter by status: `RUNNING`, `PAUSED_APPROVAL`, `COMPLETED`, `FAILED` |

=== "curl"

    ```bash
    # List all running runs
    curl https://api.runagents.io/runs \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"

    # Filter by agent
    curl "https://api.runagents.io/runs?agent_id=payment-agent" \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"

    # Filter by status
    curl "https://api.runagents.io/runs?status=PAUSED_APPROVAL" \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "conversation_id": "conv-abc123",
    "agent_id": "payment-agent",
    "namespace": "agent-system",
    "user_id": "user@example.com",
    "status": "RUNNING",
    "created_at": "2026-02-23T10:00:00Z",
    "updated_at": "2026-02-23T10:00:00Z"
  }
]
```

---

## Get Run Details

<span class="method-get">GET</span> <span class="endpoint">/runs/:id</span>

Retrieve details for a specific run.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Run ID |

=== "curl"

    ```bash
    curl https://api.runagents.io/runs/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "conversation_id": "conv-abc123",
  "agent_id": "payment-agent",
  "namespace": "agent-system",
  "user_id": "user@example.com",
  "status": "PAUSED_APPROVAL",
  "blocked_action_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-02-23T10:00:00Z",
  "updated_at": "2026-02-23T10:01:30Z"
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `run {id} not found` | Run does not exist |

---

## Update Run Status

<span class="method-patch">PATCH</span> <span class="endpoint">/runs/:id</span>

Update the status of a run. Only valid state transitions are allowed.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Run ID |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | New status: `COMPLETED`, `FAILED`, `PAUSED_APPROVAL`, or `RUNNING` |

=== "curl"

    ```bash
    curl -X PATCH https://api.runagents.io/runs/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"status": "COMPLETED"}'
    ```

### Response (200 OK)

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "agent_id": "payment-agent",
  "status": "COMPLETED",
  "updated_at": "2026-02-23T10:05:00Z"
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `run {id} not found` | Run does not exist |
| `409` | `invalid transition from {current} to {new}` | Invalid status transition |

### Valid State Transitions

```
RUNNING --> PAUSED_APPROVAL
RUNNING --> COMPLETED
RUNNING --> FAILED
PAUSED_APPROVAL --> RUNNING
PAUSED_APPROVAL --> FAILED
```

---

## Add Event

<span class="method-post">POST</span> <span class="endpoint">/runs/:id/events</span>

Append an event to a run's audit log. Sequence numbers are assigned automatically by the server.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Run ID |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Event type (see [Event Types](#event-types)) |
| `payload_hash` | string | No | SHA-256 hash of the event payload |
| `actor` | string | No | Who triggered this event (user ID or agent ID) |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/runs/f47ac10b-58cc-4372-a567-0e02b2c3d479/events \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "type": "TOOL_REQUEST",
        "actor": "payment-agent"
      }'
    ```

### Response (201 Created)

```json
{
  "event_id": "e1f2a3b4-c5d6-7890-abcd-ef1234567890",
  "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "seq": 3,
  "type": "TOOL_REQUEST",
  "actor": "payment-agent",
  "timestamp": "2026-02-23T10:01:00Z"
}
```

### Event Types

| Type | Description |
|------|-------------|
| `USER_MESSAGE` | User sent a message to the agent |
| `AGENT_MESSAGE` | Agent produced a response |
| `TOOL_REQUEST` | Agent initiated a tool call |
| `TOOL_RESPONSE` | Tool returned a response |
| `APPROVAL_REQUIRED` | Tool call blocked pending approval |
| `APPROVED` | Blocked action was approved |
| `REJECTED` | Blocked action was rejected |
| `RESUMED` | Agent resumed after approval |
| `COMPLETED` | Run completed successfully |
| `FAILED` | Run failed |

---

## List Events

<span class="method-get">GET</span> <span class="endpoint">/runs/:id/events</span>

List all events for a run, ordered by sequence number.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Run ID |

=== "curl"

    ```bash
    curl https://api.runagents.io/runs/f47ac10b-58cc-4372-a567-0e02b2c3d479/events \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
[
  {
    "event_id": "aaa-111",
    "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "seq": 1,
    "type": "USER_MESSAGE",
    "actor": "user@example.com",
    "timestamp": "2026-02-23T10:00:00Z"
  },
  {
    "event_id": "bbb-222",
    "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "seq": 2,
    "type": "TOOL_REQUEST",
    "actor": "payment-agent",
    "timestamp": "2026-02-23T10:00:05Z"
  },
  {
    "event_id": "ccc-333",
    "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "seq": 3,
    "type": "APPROVAL_REQUIRED",
    "timestamp": "2026-02-23T10:00:06Z"
  }
]
```

---

## Create Blocked Action

<span class="method-post">POST</span> <span class="endpoint">/runs/:id/actions</span>

Create a blocked action for a tool call that requires approval. This automatically pauses the run and appends an `APPROVAL_REQUIRED` event.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Run ID |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_id` | string | Yes | Name of the tool being called |
| `capability` | string | No | Specific capability being invoked |
| `payload_hash` | string | No | SHA-256 hash of the action payload (used for approval integrity) |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/runs/f47ac10b-58cc-4372-a567-0e02b2c3d479/actions \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "tool_id": "stripe-api",
        "capability": "create-charge",
        "payload_hash": "sha256:a1b2c3d4..."
      }'
    ```

### Response (201 Created)

```json
{
  "action_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "tool_id": "stripe-api",
  "capability": "create-charge",
  "payload_hash": "sha256:a1b2c3d4...",
  "status": "BLOCKED",
  "created_at": "2026-02-23T10:01:00Z",
  "updated_at": "2026-02-23T10:01:00Z"
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `run {id} not found` | Run does not exist |
| `409` | `run is {status}, must be RUNNING to create actions` | Run is not in RUNNING state |

---

## Get Action Status

<span class="method-get">GET</span> <span class="endpoint">/runs/:id/actions/:action_id</span>

Check the status of a blocked action.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Run ID |
| `action_id` | string | Action ID |

=== "curl"

    ```bash
    curl https://api.runagents.io/runs/f47ac10b-58cc-4372-a567-0e02b2c3d479/actions/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "action_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "tool_id": "stripe-api",
  "capability": "create-charge",
  "payload_hash": "sha256:a1b2c3d4...",
  "status": "BLOCKED",
  "created_at": "2026-02-23T10:01:00Z",
  "updated_at": "2026-02-23T10:01:00Z"
}
```

### Action Statuses

| Status | Description |
|--------|-------------|
| `BLOCKED` | Awaiting approval |
| `APPROVED` | Approved, pending execution |
| `EXECUTED` | Successfully executed after approval |
| `FAILED` | Execution failed |
| `EXPIRED` | Approval window expired |

---

## Approve Action

<span class="method-post">POST</span> <span class="endpoint">/runs/:id/actions/:action_id/approve</span>

Approve a blocked action. If the action has a `payload_hash`, the approval must include the same hash to ensure the approved action matches what was originally requested.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Run ID |
| `action_id` | string | Action ID |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payload_hash` | string | Conditional | Must match the action's `payload_hash` if one was set |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/runs/f47ac10b-58cc-4372-a567-0e02b2c3d479/actions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/approve \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"payload_hash": "sha256:a1b2c3d4..."}'
    ```

### Response (200 OK)

```json
{
  "action_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "run_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "tool_id": "stripe-api",
  "status": "APPROVED",
  "updated_at": "2026-02-23T10:05:00Z"
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `action {id} not found` | Action does not exist |
| `409` | `action is {status}, must be BLOCKED to approve` | Action is not in BLOCKED state |
| `409` | `payload_hash mismatch` | Provided hash does not match the action's original hash |

!!! warning "Payload Hash Integrity"
    When an action is created with a `payload_hash`, the approval request **must** include the same hash. This prevents approving a different action than what was originally blocked. A `409 Conflict` is returned on mismatch.

---

## Complete Example: Run Lifecycle

Here is a complete flow showing a run that gets blocked on a tool call, approved, and completed:

=== "curl"

    ```bash
    # 1. Create a run
    RUN=$(curl -s -X POST https://api.runagents.io/runs \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "agent_id": "payment-agent",
        "user_id": "admin@example.com",
        "namespace": "agent-system"
      }')
    RUN_ID=$(echo $RUN | jq -r '.id')
    echo "Run created: $RUN_ID"

    # 2. Add events as the agent works
    curl -s -X POST https://api.runagents.io/runs/$RUN_ID/events \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"type": "USER_MESSAGE", "actor": "admin@example.com"}'

    curl -s -X POST https://api.runagents.io/runs/$RUN_ID/events \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"type": "TOOL_REQUEST", "actor": "payment-agent"}'

    # 3. Agent hits a restricted tool -- create blocked action
    ACTION=$(curl -s -X POST https://api.runagents.io/runs/$RUN_ID/actions \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "tool_id": "stripe-api",
        "capability": "create-charge",
        "payload_hash": "sha256:abc123"
      }')
    ACTION_ID=$(echo $ACTION | jq -r '.action_id')
    echo "Action blocked: $ACTION_ID"

    # 4. Run is now PAUSED_APPROVAL -- verify
    curl -s https://api.runagents.io/runs/$RUN_ID \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq '.status'
    # "PAUSED_APPROVAL"

    # 5. Admin approves the action
    curl -s -X POST https://api.runagents.io/runs/$RUN_ID/actions/$ACTION_ID/approve \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"payload_hash": "sha256:abc123"}'

    # 6. Agent resumes and completes
    curl -s -X PATCH https://api.runagents.io/runs/$RUN_ID \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"status": "COMPLETED"}'

    # 7. View full event timeline
    curl -s https://api.runagents.io/runs/$RUN_ID/events \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" | jq '.[].type'
    # "USER_MESSAGE"
    # "TOOL_REQUEST"
    # "APPROVAL_REQUIRED"
    # "APPROVED"
    ```

---

## Run Object Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique run ID (UUID) |
| `conversation_id` | string | Conversation/session grouping ID |
| `agent_id` | string | Agent name |
| `namespace` | string | Agent namespace |
| `user_id` | string | User who triggered the run |
| `status` | string | Current status |
| `blocked_action_id` | string | ID of the action blocking this run (when paused) |
| `invoke_url` | string | Agent's invoke endpoint |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

### Run Status State Machine

| Status | Description |
|--------|-------------|
| `RUNNING` | Agent is actively executing |
| `PAUSED_APPROVAL` | Agent is paused waiting for an action to be approved |
| `COMPLETED` | Run finished successfully |
| `FAILED` | Run encountered an error |
