---
title: Architecture
description: High-level overview of how RunAgents processes requests through three stages — ingress, runtime, and egress — to deliver secure agent execution.
---

# Architecture

RunAgents processes every agent interaction through three stages: **Ingress**, **Runtime**, and **Egress**. Together, they ensure that user identity, access policy, and credentials are handled transparently — so you can focus on writing agent logic, not security plumbing.

```
Client App ──JWT──> [RunAgents Ingress] ──X-End-User-ID──> Agent
                                                              |
                                              ┌───────────────┤
                                              v               v
                                         [LLM Gateway]   [Tool Proxy]
                                              |               |
                                              v               v
                                         Model Provider   External API
                                         (OpenAI, etc.)   (Stripe, etc.)
```

---

## Stage 1: Ingress (Client to Agent)

Client applications authenticate users via JWT. When a request reaches RunAgents, the platform:

1. **Validates the JWT** -- Signature is verified against the identity provider's JWKS endpoint. Audience and issuer claims are checked.
2. **Extracts user identity** -- A configurable claim (e.g., `email`, `sub`) is pulled from the token payload.
3. **Injects the identity header** -- The extracted value is set as `X-End-User-ID` on all requests forwarded to the agent.
4. **Enforces domain-level access** -- Only client applications from allowed domains can reach the agent.

!!! info "No tokens in agent code"

    Your agent never sees the raw JWT. It receives the verified user identity as a simple HTTP header. This prevents token leakage and removes the need for JWT libraries in your agent code.

---

## Stage 2: Runtime (Agent Executes)

Once the request reaches the agent, it runs with everything it needs already injected:

| Injected Resource | How It Works |
|---|---|
| **System prompt** | Loaded from agent configuration; available to the agent at startup |
| **Tool URLs** | Each required tool is exposed as an environment variable (e.g., `TOOL_STRIPE_URL`) |
| **LLM Gateway URL** | A single endpoint for all model inference, regardless of provider |
| **Model settings** | Model name and provider per role (e.g., `LLM_MODEL_DEFAULT`, `LLM_PROVIDER_DEFAULT`) |

The agent calls tools at their registered URLs and the LLM gateway for model inference. No API keys appear in agent code -- the platform manages all credentials.

!!! tip "Write code, not configuration"

    From your agent's perspective, calling a tool is a standard HTTP request to a URL. RunAgents intercepts the call on the way out and handles authentication, authorization, and identity forwarding.

---

## Stage 3: Egress (Agent to Tool)

Every outbound call from an agent is intercepted by the platform's security mesh. The platform performs the following checks on each request:

### 1. Tool Identification

The platform matches the destination host against registered tools. If the host is not recognized, the request is blocked.

### 2. Agent Identity Verification

The agent's service identity (a unique identifier per agent, separate from the end-user identity) is extracted and verified. This ensures the platform knows *which* agent is making the request.

### 3. Policy Evaluation

The platform checks whether the agent has a valid policy binding for the target tool:

- **Allowed** -- Proceed to the next step
- **Denied, approval required** -- Create an access request, pause the run, return `APPROVAL_REQUIRED`
- **Denied, no approval path** -- Return `403 Forbidden`

### 4. Capability Enforcement

If the tool declares specific capabilities (method + path pairs), the platform verifies the request matches at least one:

- `GET /v1/charges` with a capability for `GET /v1/charges` -- allowed
- `DELETE /v1/charges` with no matching capability -- blocked

If no capabilities are declared on the tool, all operations are allowed (passthrough).

### 5. Token Injection

For allowed requests, the platform injects the correct authentication credentials:

- **API Key** -- `Authorization: Bearer <key>` header added
- **OAuth2** -- Access token retrieved (or refreshed) and injected
- **AWS Signature** -- SigV4 signing applied
- **No auth** -- Request passed through as-is

### 6. Identity Forwarding

The `X-End-User-ID` header from Stage 1 is forwarded to the external tool, so the downstream API knows which user the agent is acting on behalf of.

---

## The Developer Experience

From your perspective as a developer, the workflow is simple:

1. **Write agent code** that calls URLs (tool endpoints and the LLM gateway)
2. **Deploy the agent** via the console, API, or CLI
3. **RunAgents handles the rest** -- identity propagation, policy enforcement, credential management, and approval workflows

You never write authentication logic, manage API keys in code, or implement policy checks. The platform does it all, transparently, on every request.

---

## Key Design Principles

| Principle | Description |
|---|---|
| **Zero-trust by default** | No outbound request from an agent reaches an external service without policy evaluation |
| **Identity at every hop** | User identity flows from client to agent to tool, never lost or forged |
| **Credentials never in code** | API keys, OAuth tokens, and signing credentials are managed by the platform and injected at the egress layer |
| **Least privilege** | Agents only access tools they are explicitly bound to, with operation-level granularity |
| **Human-in-the-loop** | High-risk operations require explicit admin approval before the agent can proceed |

---

## Next Steps

- [Identity Propagation](identity-propagation.md) -- Deep dive into how user identity flows end-to-end
- [Policy Model](policy-model.md) -- Understand how access control rules are structured and evaluated
- [OAuth & Consent](oauth-consent.md) -- How RunAgents handles OAuth2 for tools that require user authorization
