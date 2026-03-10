---
title: RunAgents — Deploy AI Agents That Act Securely
description: Deploy AI agents that call external tools and APIs with enterprise-grade security. Identity propagation, zero-trust networking, just-in-time approvals, and OAuth consent — all managed for you.
hide:
  - navigation
  - toc
---

<div class="ra-hero" markdown>

# Deploy AI Agents That Act Securely

Upload your agent code. Wire it to tools. RunAgents handles identity, access control, and approvals — automatically.

<div class="ra-hero-buttons" markdown>
<a href="getting-started/quickstart/" class="ra-btn-primary">🚀 Get Started Free</a>
<a href="getting-started/cli-quickstart/" class="ra-btn-secondary">⌨️ CLI Quickstart</a>
<a href="concepts/architecture/" class="ra-btn-secondary">📐 Architecture</a>
</div>

</div>

<div class="ra-cards" markdown>

<a href="getting-started/quickstart/" class="ra-card" markdown>
<span class="ra-card-icon">🚀</span>
### 5-Minute Quickstart
Deploy your first agent from the console. No infrastructure required.
</a>

<a href="getting-started/cli-quickstart/" class="ra-card" markdown>
<span class="ra-card-icon">⌨️</span>
### CLI & Copilot
`runagents copilot` — deploy agents in natural language from your terminal.
</a>

<a href="getting-started/deploy-from-ai-tools/" class="ra-card" markdown>
<span class="ra-card-icon">🤖</span>
### Claude Code / Codex
Use the action plan workflow to deploy directly from your AI coding tool.
</a>

<a href="platform/approvals/" class="ra-card" markdown>
<span class="ra-card-icon">🛡️</span>
### Just-In-Time Approvals
High-risk tool calls pause for admin review. Slack, PagerDuty, Teams integrations.
</a>

<a href="concepts/policy-model/" class="ra-card" markdown>
<span class="ra-card-icon">🔐</span>
### Policy-Driven Access
Fine-grained allow/deny rules on every outbound agent call.
</a>

<a href="api/runs/" class="ra-card" markdown>
<span class="ra-card-icon">📊</span>
### Run Observability
Full audit trail per run — USER_MESSAGE events, tool calls, approvals, exports.
</a>

</div>

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
     |                     |  ✓ policy checked             |
     |                     |  ✓ token injected             |
     |                     |  ✓ identity forwarded         |
     |                     |                               |
     |                     |<-- tool response -------------|
     |<--- response -------|                               |
```

Every outbound call from your agent is intercepted, authorized against your policies, enriched with the correct credentials, and forwarded — all transparently.

---

## Three Pillars

=== ":material-account-arrow-right: Identity Propagation"

    User identity flows from client → agent → external tool automatically.
    Every downstream service sees **who** made the request, not just which service account.

    - JWT validated at ingress, user ID extracted into `X-End-User-ID` header
    - Tools receive the real end-user identity on every call
    - Full traceability across the entire request chain

=== ":material-shield-lock: Policy-Driven Access"

    Fine-grained allow/deny rules control which agents can call which tools, at which paths.

    - Policies define resource URN patterns with allow or deny effects
    - Auto-binding creates policies when you deploy an agent with required tools
    - Capability checks enforce operation-level restrictions (e.g. `GET /docs/*` only)

=== ":material-clipboard-check: Just-In-Time Approvals"

    High-risk tools pause the agent until an admin approves. No manual re-triggering needed.

    - Admin notified via Slack, PagerDuty, Teams, or Jira
    - Payload hash integrity ensures approved request matches what the agent will send
    - Platform automatically resumes the agent after approval

---

## Ready to Try?

<div style="text-align:center;margin:2rem 0" markdown>
[🚀 Start Free Trial](https://try.runagents.io){ .cta-button }
&nbsp;&nbsp;
[📖 Read the Quickstart](getting-started/quickstart.md){ .md-button }
</div>

<small>© 2026 RunAgents, Inc. · [Privacy](https://runagents.io/privacy) · [Terms](https://runagents.io/terms)</small>
