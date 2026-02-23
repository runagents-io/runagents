# Registering Tools

Tools are the external APIs and services your agents call -- Stripe for payments, GitHub for code, Slack for notifications, or any HTTP endpoint. Registering a tool tells RunAgents how to reach it, how to authenticate, and who is allowed to use it.

Navigate to **Tools** in the sidebar, then click **+ New Tool**.

---

## Tool Configuration

### Basic Information

| Field | Description | Required |
|-------|-------------|----------|
| **Name** | Unique identifier for the tool (e.g., `stripe-api`, `github-api`) | Yes |
| **Description** | What the tool does (shown in the deploy wizard during wiring) | No |

### Location

| Option | When to use |
|--------|------------|
| **External** | SaaS APIs and services outside your network (e.g., `https://api.stripe.com`) |
| **Internal** | Services running inside your own network |

### Connection

| Field | Description | Required |
|-------|-------------|----------|
| **Base URL** | The tool's API endpoint (e.g., `https://api.stripe.com`) | Yes |
| **Port** | Target port number (defaults to 443 for HTTPS) | No |
| **Protocol** | HTTPS or HTTP | No |

---

## Authentication

Choose how RunAgents authenticates when your agent calls this tool.

### None

No authentication is added to requests. Use for public APIs or internal services with network-level security.

### API Key

An API key is injected into each request automatically. Your agent code never sees the key.

| Field | Description |
|-------|-------------|
| **Location** | Where to inject the key: `Header` or `Query` parameter |
| **Header / Parameter name** | The name of the header or query param (e.g., `Authorization`, `X-API-Key`) |
| **Value prefix** | Text prepended to the key value (e.g., `Bearer ` for `Authorization: Bearer sk-xxx`) |
| **Secret** | The stored secret containing the API key |

### OAuth2

Full OAuth2 flow with automatic token management. The platform handles token refresh and per-user consent.

| Field | Description |
|-------|-------------|
| **Authorization URL** | The OAuth2 authorization endpoint |
| **Token URL** | The OAuth2 token endpoint |
| **Scopes** | OAuth2 scopes to request (comma-separated) |
| **Client credentials** | The secret containing `client_id` and `client_secret` |

!!! info "Per-user OAuth consent"
    When a tool uses OAuth2 with an authorization URL, RunAgents manages per-user consent. The first time a user's agent accesses the tool, they are redirected to the provider's consent screen. After granting access, a per-user refresh token is stored and used automatically for subsequent requests.

---

## Access Control

Access control determines which agents can call this tool and whether admin approval is needed.

| Mode | Behavior |
|------|----------|
| **Open** | Any agent that lists this tool in its configuration gets automatic access. No approval needed. |
| **Restricted** | Access requires an explicit policy binding. Agents must be granted access by an admin. |
| **Critical** | Requires just-in-time (JIT) admin approval for each access. Requests are paused until approved. See [Approvals](approvals.md). |

### Approval Settings

When access control is set to **Critical** (or `requireApproval` is enabled), configure the approval workflow:

| Field | Description | Default |
|-------|-------------|---------|
| **Approval group** | The admin group that reviews access requests (e.g., `sec-ops`) | -- |
| **Default access window** | How long approved access lasts (e.g., `4h`, `24h`) | 4 hours |
| **Auto-expire** | Automatically revoke access after the window expires | Yes |

---

## Capabilities

Capabilities define the specific operations a tool exposes. When capabilities are declared, RunAgents enforces that agent requests match at least one declared operation. If no capabilities are defined, all operations are allowed (passthrough).

Each capability has:

| Field | Description |
|-------|-------------|
| **Name** | A descriptive identifier (e.g., `charges.create`) |
| **HTTP Method** | The allowed method (`GET`, `POST`, `PUT`, `DELETE`, etc.) |
| **Path** | The URL path prefix for this operation (e.g., `/v1/charges`) |
| **Description** | What this operation does |
| **Risk tags** | Labels like `financial`, `pii`, `destructive` for this specific operation |

!!! note "Capabilities as an allow-list"
    When you define capabilities, they act as an **allow-list**. If an agent tries to call a path or method not covered by any declared capability, the request is denied with a `403 operation not permitted` error. Leave capabilities empty to allow all operations.

---

## Risk Tags

Label a tool with risk categories to surface in dashboards and audit logs:

- `pii` -- tool handles personally identifiable information
- `financial` -- tool processes payments or financial data
- `destructive` -- tool can delete or modify data irreversibly
- Custom tags as needed

Risk tags can also be set per-capability for more granular labeling.

---

## Example: Registering the Stripe API

Here is a complete example of registering the Stripe API as a tool with API key authentication, restricted access, and declared capabilities.

**Basic Information:**

| Field | Value |
|-------|-------|
| Name | `stripe-api` |
| Description | Stripe payments API for creating and listing charges |
| Location | External |
| Base URL | `https://api.stripe.com` |

**Authentication:**

| Field | Value |
|-------|-------|
| Type | API Key |
| Location | Header |
| Header name | `Authorization` |
| Value prefix | `Bearer ` |
| Secret | `stripe-api-key` (a secret you previously stored containing your Stripe secret key) |

**Access Control:**

| Field | Value |
|-------|-------|
| Mode | Restricted |

**Capabilities:**

| Name | Method | Path | Description | Risk Tags |
|------|--------|------|-------------|-----------|
| `charges.create` | `POST` | `/v1/charges` | Create a new charge | `financial` |
| `charges.list` | `GET` | `/v1/charges` | List all charges | -- |

With this configuration:

- Only agents explicitly granted access can call the Stripe API
- Agents can only call `POST /v1/charges` and `GET /v1/charges` -- any other endpoint is blocked
- The platform injects the `Authorization: Bearer sk-xxx` header automatically
- Your agent code never handles or stores the Stripe API key

---

## Editing a Tool

To edit an existing tool, navigate to **Tools**, click on the tool name, then click **Edit**. All fields are editable. Changes take effect immediately for all agents using the tool.

---

## Tool Status

| Status | Meaning |
|--------|---------|
| **Available** | Tool endpoint is reachable and responding |
| **Pending** | Tool was just registered; platform resources are being configured |
| **Unavailable** | Tool endpoint is unreachable (check the base URL and network connectivity) |

The platform periodically probes external tool endpoints and updates the status automatically.

---

## Built-in Echo Tool

The **echo-tool** is a built-in demo tool included in the RunAgents starter kit. It is created when you click **Deploy Hello World Agent** on the Dashboard or **Add starter Echo Tool** on the Tools page.

- **Location**: Internal
- **Base URL**: Points to the platform's built-in echo endpoint
- **Access Control**: Open (any agent can use it)
- **Authentication**: None

The echo tool accepts `POST` requests with a JSON body `{"message": "..."}` and echoes the message back. It is designed for testing the deploy flow without any external dependencies.

!!! tip "Try RunAgents free"
    Want to register your own tools and deploy production agents? Contact us at **[try@runagents.io](mailto:try@runagents.io)** to get started with a free trial.

---

## What's Next

| Goal | Where to go |
|------|------------|
| Deploy an agent that uses this tool | [Deploying Agents](deploying-agents.md) |
| Configure LLM access | [Model Providers](model-providers.md) |
| Set up the approval workflow | [Approvals](approvals.md) |
