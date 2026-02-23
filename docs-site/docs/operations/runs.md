---
title: Run Lifecycle
description: How agent runs are created, tracked, paused for approval, and resumed in RunAgents, including events, blocked actions, and payload integrity.
---

# Run Lifecycle

A **run** represents a single invocation of an agent -- from the initial request to completion. RunAgents tracks every run through a defined state machine, logs events, and manages approval workflows when the agent encounters a restricted tool.

---

## Creating a Run

Runs are created when an agent is invoked, either through:

- A client application sending a request to the agent's endpoint
- An API call to the agent's invoke URL
- A background trigger or scheduled invocation

Each run is assigned a unique ID and begins in the `RUNNING` state.

---

## Run States

| Status | Description |
|---|---|
| `RUNNING` | The agent is actively executing |
| `PAUSED_APPROVAL` | The agent hit a tool that requires approval; execution is paused until an admin approves or rejects |
| `COMPLETED` | The agent finished successfully |
| `FAILED` | The agent encountered an error |

### State Transitions

```
                 ┌──────────────────────────────────┐
                 |                                  |
                 v                                  |
RUNNING ───> PAUSED_APPROVAL ───(approved)───> RUNNING
   |                |
   v                v
COMPLETED       FAILED

RUNNING ───> FAILED
RUNNING ───> COMPLETED
```

!!! info "Only forward transitions"

    Runs follow a strict state machine. A `COMPLETED` or `FAILED` run cannot be restarted. A `PAUSED_APPROVAL` run can only transition to `RUNNING` (on approval) or `FAILED` (on rejection or timeout).

---

## Events

Every run has an ordered **event log** that records what happened during execution. Events are automatically sequenced -- each event gets a monotonically increasing sequence number.

| Event Type | Description |
|---|---|
| `TOOL_CALL` | Agent called an external tool |
| `LLM_CALL` | Agent called the LLM gateway |
| `APPROVAL_REQUIRED` | Agent's tool call was blocked pending approval |
| `APPROVAL_GRANTED` | Admin approved the access request |
| `APPROVAL_REJECTED` | Admin rejected the access request |
| `ERROR` | An error occurred during execution |
| `COMPLETED` | Run finished successfully |

Events provide a complete audit trail of agent behavior. Use them for debugging, compliance, and understanding agent decision-making.

### Viewing Events

=== "Console"

    Navigate to **Agents** > select your agent > **Runs** tab > select a run. The event timeline shows all events in order.

=== "API"

    ```bash
    # List events for a run
    curl https://your-platform/runs/{run_id}/events
    ```

---

## Blocked Actions and Approval Workflow

When an agent calls a tool that requires approval, the following sequence occurs:

### 1. Request Blocked

The platform intercepts the tool call and determines that the agent does not have an active policy binding, and the tool requires approval.

### 2. Blocked Action Created

A **blocked action** is created with:

| Field | Description |
|---|---|
| `tool` | The name of the tool the agent tried to call |
| `capability` | The specific operation (method + path) |
| `payload_hash` | A SHA-256 hash of the request body |
| `status` | Initially `PENDING` |

### 3. Run Paused

The run transitions to `PAUSED_APPROVAL`. An `APPROVAL_REQUIRED` event is logged with the details of the blocked action.

### 4. Admin Reviews

Administrators can see pending approvals in the console (**Approvals** page) or via the API. Each approval request shows:

- Which agent is requesting access
- Which tool and operation
- The payload hash (for integrity verification)
- When the request was created

### 5. Approval or Rejection

=== "Approve"

    The admin approves the request. A time-limited policy binding is created for the agent + tool combination. The blocked action status changes to `APPROVED`.

=== "Reject"

    The admin rejects the request. The blocked action status changes to `REJECTED`. The run transitions to `FAILED`.

### 6. Automatic Resumption

After approval, a background worker detects the approved action and automatically:

1. Invokes the agent to resume execution
2. Marks the blocked action as `EXECUTED`
3. Transitions the run back to `RUNNING`
4. Logs an `APPROVAL_GRANTED` event

The agent retries the tool call, which now succeeds because the policy binding exists.

!!! tip "No manual intervention needed after approval"

    Once an admin approves the request, the platform automatically resumes the agent. There is no need to manually re-trigger the run.

---

## Payload Hash Integrity

Blocked actions include a cryptographic hash of the original request payload. This serves as a tamper-detection mechanism:

- When the admin approves the action, the hash is recorded
- When the agent resumes and retries the tool call, the platform verifies the payload hash matches
- If the payload has changed (e.g., the agent modified the request), the call is rejected with a `409 Conflict`

This prevents a scenario where an agent modifies its request after receiving approval for a different payload.

!!! warning "Hash mismatch = rejection"

    If the payload hash does not match, the retried call fails even though the action was approved. The agent must submit the exact same request that was originally blocked.

---

## Run Correlation

When a tool call is blocked and an approval is needed, RunAgents correlates the access request with the run:

- The `run_id` is attached to the access request
- The blocked action is linked to both the run and the access request
- Events reference the action ID for traceability

This allows you to trace from a run event back to the approval decision, and from an approval back to the specific run that triggered it.

---

## Viewing Runs

=== "Console"

    - **Agent Detail page** > **Runs** tab: See all runs for a specific agent
    - **Dashboard**: See recent runs across all agents
    - Each run shows its status, duration, and event count
    - Click a run to see the full event timeline

=== "API"

    ```bash
    # List all runs
    curl https://your-platform/runs

    # Get a specific run
    curl https://your-platform/runs/{run_id}

    # List events for a run
    curl https://your-platform/runs/{run_id}/events

    # Get a blocked action
    curl https://your-platform/runs/{run_id}/actions/{action_id}
    ```

---

## Summary

| Concept | Description |
|---|---|
| **Run** | A single agent invocation with a unique ID and state |
| **State machine** | `RUNNING` > `PAUSED_APPROVAL` > `RUNNING` > `COMPLETED` or `FAILED` |
| **Events** | Ordered log of everything that happened during a run |
| **Blocked action** | A tool call that was intercepted pending approval |
| **Payload hash** | Tamper detection ensuring the approved request matches the retried request |
| **Auto-resumption** | Background worker automatically resumes the agent after approval |

---

## Next Steps

- [Policy Model](../concepts/policy-model.md) -- Understand how access control modes trigger the approval workflow
- [Troubleshooting](troubleshooting.md) -- Common run issues and how to resolve them
