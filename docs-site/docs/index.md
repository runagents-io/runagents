---
title: RunAgents — Deploy AI Agents That Act Securely
description: Deploy AI agents that call external tools and APIs with enterprise-grade security. Identity propagation, zero-trust networking, just-in-time approvals, and OAuth consent — all managed for you.
---

# RunAgents — Deploy AI Agents That Act Securely

**Deploy AI agents that can call external tools, APIs, and SaaS services — with enterprise-grade security built in.**

RunAgents is a managed platform for deploying and orchestrating AI agents. Upload your agent code, wire it to the tools and LLMs it needs, and RunAgents handles identity propagation, access control, OAuth consent, and networking. No infrastructure to manage.

---

## Why RunAgents?

AI agents are powerful when they can _act_ — call APIs, read databases, trigger workflows. But giving an agent access to external services introduces serious security concerns:

- **Who is the agent acting on behalf of?** User identity must flow end-to-end.
- **What is the agent allowed to do?** Access must be scoped and auditable.
- **What happens when an agent requests something sensitive?** High-risk actions need human approval.

RunAgents solves all three.

---

## Three Pillars of Secure Agent Deployment

### :material-account-arrow-right: Identity Propagation

User identity flows from client application to agent to external tool — automatically. When a user triggers an agent, RunAgents ensures the downstream tool knows _who_ is making the request. No identity is lost at any hop.

- Tokens validated at ingress
- User ID extracted and forwarded as headers
- Tools see the real end-user, not a service account

### :material-shield-lock: Policy-Driven Access

Fine-grained allow/deny rules control which agents can call which tools. Policies are evaluated in real time on every outbound request.

- Policies define resource patterns with allow or deny effects
- Policy bindings link agents and users to policies
- Auto-binding creates policies automatically when you deploy an agent with its required tools
- Capability checks enforce operation-level restrictions (e.g., only `GET /documents/*`, not `DELETE`)

### :material-clipboard-check: Just-In-Time Approvals

For high-risk tools, access is not automatic. The platform pauses the agent, notifies an admin, and waits for explicit approval before the agent proceeds — with a time-limited window.

- Tools can be marked as requiring approval
- When an agent tries to call a restricted tool, a request is created and the run is paused
- Admins approve or reject from the console or API
- Approved access expires after a configurable TTL

---

## How It Works

```
 Client App           RunAgents Platform              External Tool
 ----------     ----------------------------         --------------
     |                     |                               |
     |--- request -------->| Agent receives request        |
     |                     | with end-user identity        |
     |                     |                               |
     |                     |--- tool call ---------------->|
     |                     |  (policy checked,             |
     |                     |   token injected,             |
     |                     |   identity forwarded)         |
     |                     |                               |
     |                     |<-- tool response -------------|
     |<--- response -------|                               |
```

Every outbound call from your agent is intercepted, authorized against your policies, enriched with the correct credentials, and forwarded — all transparently.

---

## Get Started

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quickstart**

    ---

    Deploy your first agent in 5 minutes using the console.

    [:octicons-arrow-right-24: Quickstart](getting-started/quickstart.md)

-   :material-api:{ .lg .middle } **API Quickstart**

    ---

    Deploy an agent programmatically with curl.

    [:octicons-arrow-right-24: API Quickstart](getting-started/api-quickstart.md)

-   :material-console:{ .lg .middle } **CLI Quickstart**

    ---

    Manage RunAgents from your terminal.

    [:octicons-arrow-right-24: CLI Quickstart](getting-started/cli-quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **Concepts**

    ---

    Understand the architecture, policy model, and identity flow.

    [:octicons-arrow-right-24: Concepts](concepts/architecture.md)

</div>

---

## Ready to Try RunAgents?

!!! tip "Start your free trial"

    RunAgents offers a free trial with full platform access. Deploy agents, register tools, and see the security model in action.

    **Get started now** — email [try@runagents.io](mailto:try@runagents.io) to request access, or log in to your console if you already have an account.

    [:material-email-outline: Request Trial Access](mailto:try@runagents.io){ .md-button .md-button--primary }
    [:material-open-in-new: Open Console](https://console.runagents.io){ .md-button }

---

<small>Built with version {{ version }}</small>
