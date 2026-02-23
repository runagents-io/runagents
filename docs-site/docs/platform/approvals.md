# Approvals

When a tool is configured with **Critical** access control, agents cannot call it without explicit admin approval. RunAgents implements a just-in-time (JIT) approval workflow that pauses the agent's request, creates an approval request, and resumes automatically once approved.

Navigate to **Approvals** in the sidebar to view and manage pending requests.

---

## How Approvals Work

### The Approval Flow

```
Agent calls tool          Platform intercepts        Admin reviews
with Critical access      and pauses request         on Approvals page
       |                         |                         |
       |-- POST /v1/charges ---->|                         |
       |                         |-- Create access ------->|
       |                         |   request (PENDING)     |
       |                         |                         |
       |<-- 403 APPROVAL --------|                         |
       |    REQUIRED             |                         |
       |                         |          Approve / Reject
       |                         |<------------------------|
       |                         |                         |
       |                         |-- Grant time-limited -->|
       |                         |   access                |
       |                         |                         |
       |-- Retry tool call ----->|                         |
       |<-- 200 OK -------------|                         |
```

1. An agent calls a tool that has **Critical** access control (or `requireApproval` enabled).
2. The platform intercepts the request and returns a `403 APPROVAL_REQUIRED` response to the agent.
3. An access request is created on the **Approvals** page with status `Pending`.
4. An admin reviews the request and clicks **Approve** or **Reject**.
5. If approved: a time-limited access grant is created (default 4 hours). The agent can retry the tool call and it will succeed.
6. If rejected: the agent receives a `403 Forbidden` on subsequent attempts.
7. After the access window expires, the grant is automatically revoked. The next call will require a new approval.

---

## The Approvals Page

The Approvals page lists all access requests with their current status. Each request shows:

| Column | Description |
|--------|-------------|
| **Requesting agent** | The agent that triggered the request |
| **Target tool** | The tool being accessed |
| **User** | The end-user identity associated with the request (if identity propagation is configured) |
| **Requested operation** | The specific capability being accessed (if the tool has declared capabilities) |
| **Status** | `Pending`, `Provisioned`, `Rejected`, `Expired`, or `Failed` |
| **Timestamp** | When the request was created |

### Approving a Request

Click on a pending request to review the details, then:

- Click **Approve** to grant access. The approval creates a time-limited policy binding.
- Optionally adjust the access duration (defaults to the tool's configured `defaultDuration`, typically 4 hours).
- Add a reason or comment for the audit trail.

### Rejecting a Request

Click **Reject** to deny access. Optionally provide a reason. The agent will continue to receive `403 Forbidden` responses when calling this tool.

---

## Access Request Lifecycle

| Phase | Meaning |
|-------|---------|
| **Pending** | Request created; awaiting admin review |
| **Provisioned** | Approved; time-limited access is active |
| **Rejected** | Admin denied the request |
| **Expired** | Access window has elapsed; the grant has been automatically revoked |
| **Failed** | An error occurred while processing the request |

```
Pending ──> Provisioned ──> Expired
   │
   └──> Rejected
```

!!! info "Automatic cleanup"
    Expired grants are automatically cleaned up by a background process. You do not need to manually revoke expired access.

---

## Integration with Runs

Approvals are tightly integrated with the **run lifecycle**. When an agent is executing within an active run:

1. The agent calls a restricted tool and receives `403 APPROVAL_REQUIRED`.
2. The platform automatically:
    - Creates a **blocked action** linked to the run
    - Pauses the run (status changes to `PAUSED_APPROVAL`)
    - Logs an `APPROVAL_REQUIRED` event in the run timeline
3. The run appears in the **Runs Awaiting Approval** section on the Dashboard.
4. An admin approves the request on the Approvals page.
5. The platform automatically:
    - Creates the time-limited access grant
    - Resumes the run
    - Re-invokes the agent to retry the blocked action
    - Logs an `APPROVED` event in the run timeline

This means the agent does not need to implement any retry logic -- the platform handles the entire pause-approve-resume cycle.

---

## Run Correlation and Audit Trail

Each approval request can be linked to a specific run and action for full traceability:

| Field | Description |
|-------|-------------|
| **Run ID** | The run that triggered the approval request |
| **Action ID** | The specific blocked action within the run |
| **Payload hash** | A hash of the request payload, ensuring the approved action matches what was originally requested |

!!! note "Payload hash verification"
    When an admin approves a blocked action, the platform verifies that the payload hash matches. This prevents an agent from modifying the request between the time it was blocked and the time it was approved. A hash mismatch results in a `409 Conflict` error.

This audit trail answers questions like:

- *Which run triggered this approval?*
- *What exact request was the agent trying to make?*
- *Who approved it, when, and with what access window?*

---

## Configuring Tools for Approval

To enable the approval workflow on a tool, set its access control to **Critical** when [registering the tool](registering-tools.md). You can also configure:

| Setting | Description | Default |
|---------|-------------|---------|
| **Access mode** | Set to `Critical` to require approval | -- |
| **Approval group** | The admin group that reviews requests (e.g., `sec-ops`, `platform-admins`) | -- |
| **Default access window** | How long approved access lasts | 4 hours |
| **Auto-expire** | Automatically revoke access after the window expires | Yes |

---

## Example: Approval Workflow for a Payments API

Scenario: You have registered the Stripe API with **Critical** access control and a 2-hour default access window.

1. An agent deployed for a customer support use case needs to issue a refund via Stripe.
2. The agent calls `POST /v1/refunds` on the Stripe tool.
3. The platform intercepts the call and creates an approval request:
    - Agent: `support-agent`
    - Tool: `stripe-api`
    - Operation: `refunds.create` (POST /v1/refunds)
    - User: `alice@company.com`
4. The approval request appears on the Approvals page and the Dashboard.
5. A `sec-ops` admin reviews the request, sees the agent, user, and operation, and clicks **Approve** with a 2-hour window.
6. The agent's run resumes, the refund call succeeds, and the run continues.
7. After 2 hours, the access grant expires automatically. The next refund attempt will require a new approval.

---

## What's Next

| Goal | Where to go |
|------|------------|
| Configure a tool with Critical access | [Registering Tools](registering-tools.md) |
| Understand identity propagation in approvals | [Identity Providers](identity-providers.md) |
| Deploy an agent that uses restricted tools | [Deploying Agents](deploying-agents.md) |
| Return to the overview | [Dashboard](dashboard.md) |
