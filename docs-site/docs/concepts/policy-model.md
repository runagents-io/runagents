---
title: Policy Model
description: How RunAgents enforces access control through policies, policy bindings, auto-binding, access control modes, and capability-level enforcement.
---

# Policy Model

RunAgents enforces access control on every outbound request from an agent. The policy model determines which agents can call which tools, at what granularity, and whether human approval is required.

---

## Core Concepts

### Policies

A **policy** defines what actions are allowed or denied. Each policy contains one or more rules:

```yaml
name: stripe-read-only
rules:
  - permission: allow
    resource: "https://api.stripe.com/v1/charges*"
    operations: [GET]
  - permission: deny
    resource: "https://api.stripe.com/v1/charges*"
    operations: [DELETE]
```

| Field | Description |
|---|---|
| `permission` | `allow` or `deny` |
| `resource` | URL pattern with wildcard support (e.g., `https://api.stripe.com/*`) |
| `operations` | Optional list of HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`). If omitted, the rule applies to all methods. |

!!! warning "Deny takes precedence"

    When both `allow` and `deny` rules match a request, the `deny` rule wins. This follows the principle of least privilege: explicitly denied actions cannot be overridden by allow rules.

### Policy Bindings

A **policy binding** links a policy to one or more subjects (identities):

```yaml
name: billing-agent-stripe-access
policy: stripe-read-only
subjects:
  - kind: ServiceAccount
    name: billing-agent
  - kind: Group
    name: finance-team
```

| Subject Kind | Description |
|---|---|
| `ServiceAccount` | An agent's identity. Each agent gets a unique service account when deployed. |
| `User` | An end-user identity (as identified by `X-End-User-ID`). |
| `Group` | A named group of users or agents. |

!!! info "Agents are identified by service account"

    When RunAgents evaluates a policy, it uses the agent's service account identity -- not the end-user's identity. This means you grant permissions to specific agents, and the platform verifies the agent's identity cryptographically on every request.

---

## Access Control Modes

Every tool registered on RunAgents has an access control mode that determines how agents gain access:

| Mode | Behavior | Best For |
|---|---|---|
| **Open** | Auto-bind on deploy. Any agent that lists this tool as required gets access automatically. | Internal tools, low-risk APIs, development environments |
| **Restricted** | Manual binding required. An admin must create a policy + policy binding to grant access. | Production APIs, third-party services with rate limits |
| **Critical** | Just-in-time approval required. Each access request needs explicit admin approval with a time-limited window. | Financial APIs, data deletion endpoints, compliance-sensitive tools |

---

## Auto-Binding (Open Tools)

When you deploy an agent with required tools, RunAgents automatically creates policies and bindings for tools that use **Open** access control:

1. Agent is deployed with `requiredTools: [echo-tool, internal-api]`
2. Both tools are configured with Open access mode
3. RunAgents creates:
    - A policy allowing the agent to call each tool's URL
    - A policy binding linking the agent's service account to the policy
4. The agent can call both tools immediately -- no manual policy setup needed

!!! tip "Auto-bindings are cleaned up automatically"

    When you delete an agent, its auto-created policies and bindings are deleted too. No orphaned policies to manage.

---

## Manual Policy Binding (Restricted Tools)

For tools with **Restricted** access, you must explicitly create policies and bindings:

=== "Console"

    1. Go to **Approvals** in the sidebar
    2. Navigate to the **Policies** tab
    3. Create a new policy with the desired rules
    4. Create a policy binding linking the policy to the agent

=== "API"

    ```bash
    # Create a policy
    curl -X POST https://your-platform/api/policies \
      -H "Content-Type: application/json" \
      -d '{
        "name": "stripe-full-access",
        "rules": [{
          "permission": "allow",
          "resource": "https://api.stripe.com/*"
        }]
      }'

    # Bind it to an agent
    curl -X POST https://your-platform/api/policy-bindings \
      -H "Content-Type: application/json" \
      -d '{
        "name": "billing-agent-stripe",
        "policy": "stripe-full-access",
        "subjects": [{
          "kind": "ServiceAccount",
          "name": "billing-agent"
        }]
      }'
    ```

---

## Just-In-Time Approvals (Critical Tools)

For tools marked as **Critical**, the platform enforces a human-in-the-loop workflow:

1. Agent calls the tool
2. Platform evaluates the policy and finds no active binding (or the tool requires approval regardless)
3. An **access request** is created with details about the agent, tool, and requested capability
4. The agent's run is paused (`PAUSED_APPROVAL` state)
5. Admin reviews and approves or rejects the request
6. If approved: a time-limited policy binding is created, the run resumes, and the agent retries the tool call
7. When the TTL expires, the binding is automatically removed

!!! warning "Time-limited access"

    Approved access for Critical tools expires after a configurable TTL (time-to-live). Once expired, the agent must request access again. This prevents long-lived permissions on sensitive tools.

See [Run Lifecycle](../operations/runs.md) for details on how runs pause and resume during approvals.

---

## Capability-Level Enforcement

Beyond URL-level policies, tools can declare specific **capabilities** -- the operations they support:

```yaml
name: stripe-tool
baseUrl: https://api.stripe.com
capabilities:
  - method: GET
    pathPattern: /v1/charges
  - method: POST
    pathPattern: /v1/charges
  - method: GET
    pathPattern: /v1/customers
```

When capabilities are declared:

- Only requests matching a declared capability (method + path prefix) are allowed
- Even if the agent has a valid policy binding, a non-matching operation is blocked
- This acts as an additional layer of defense beyond policy rules

**Example**: An agent with full `allow` access to `https://api.stripe.com/*` calls `DELETE /v1/charges/ch_123`. If the tool only declares `GET` and `POST` capabilities, the `DELETE` request is blocked with `403 operation not permitted`.

!!! info "Empty capabilities = passthrough"

    If a tool does not declare any capabilities, all operations are allowed (subject to policy evaluation). Capabilities are an opt-in restriction for tools where you want operation-level granularity.

---

## Policy Evaluation Order

When an agent makes an outbound request, the platform evaluates access in this order:

1. **Tool identification** -- Match the destination host to a registered tool. If no match, deny.
2. **Agent identification** -- Verify the agent's service identity.
3. **Policy binding lookup** -- Find all policy bindings for this agent + tool combination.
4. **Rule evaluation** -- Evaluate all matching rules. Deny takes precedence over allow.
5. **Capability check** -- If the tool declares capabilities, verify the method + path matches.
6. **Approval check** -- If denied and the tool requires approval, create an access request instead of a hard deny.

---

## Summary

| Concept | Purpose |
|---|---|
| **Policy** | Defines allow/deny rules for resources (URL patterns) and operations (HTTP methods) |
| **Policy Binding** | Links a policy to agents, users, or groups |
| **Auto-Binding** | Automatic policy creation for Open tools when agents are deployed |
| **Access Modes** | Open (auto), Restricted (manual), Critical (approval required) |
| **Capabilities** | Operation-level allow-lists on tools (method + path) |
| **TTL Expiry** | Time-limited access for approved Critical tool bindings |

---

## Next Steps

- [OAuth & Consent](oauth-consent.md) -- How authentication works alongside policy enforcement
- [Run Lifecycle](../operations/runs.md) -- How approval workflows integrate with run state management
- [Architecture](architecture.md) -- See where policy evaluation happens in the three-stage flow
