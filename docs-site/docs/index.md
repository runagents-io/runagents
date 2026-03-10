---
title: RunAgents — Deploy AI Agents That Act Securely
description: Deploy AI agents that call external tools and APIs with enterprise-grade security. Identity propagation, zero-trust networking, just-in-time approvals, and OAuth consent — all managed for you.
hide:
  - navigation
  - toc
---

<div class="ra-hero">
  <h1>Deploy AI Agents That Act Securely</h1>
  <p>Upload your agent code. Wire it to tools and LLMs. RunAgents handles identity propagation, access control, and just-in-time approvals — automatically.</p>
  <div class="ra-hero-buttons">
    <a href="getting-started/quickstart/" class="ra-btn-primary">Get Started Free</a>
    <a href="getting-started/cli-quickstart/" class="ra-btn-secondary">CLI Quickstart</a>
    <a href="concepts/architecture/" class="ra-btn-secondary">Architecture</a>
  </div>
</div>

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **5-Minute Quickstart**

    ---

    Deploy your first agent from the console. No infrastructure required.

    [:octicons-arrow-right-24: Get started](getting-started/quickstart.md)

-   :material-console-line:{ .lg .middle } **CLI & Copilot**

    ---

    `runagents copilot` — deploy and manage agents in natural language from your terminal.

    [:octicons-arrow-right-24: CLI quickstart](getting-started/cli-quickstart.md)

-   :material-robot-outline:{ .lg .middle } **Claude Code & Codex**

    ---

    Generate action plans with your AI coding tool and apply them with one command.

    [:octicons-arrow-right-24: Deploy from AI tools](getting-started/deploy-from-ai-tools.md)

-   :material-shield-check-outline:{ .lg .middle } **Just-In-Time Approvals**

    ---

    High-risk tool calls pause for admin review. Slack, PagerDuty, and Teams integrations built in.

    [:octicons-arrow-right-24: Approvals](platform/approvals.md)

-   :material-lock-outline:{ .lg .middle } **Policy-Driven Access**

    ---

    Fine-grained allow/deny rules enforced on every outbound agent call, at method + path level.

    [:octicons-arrow-right-24: Policy model](concepts/policy-model.md)

-   :material-chart-timeline-variant:{ .lg .middle } **Run Observability**

    ---

    Full audit trail per run — message events, tool calls, approvals, and export to Splunk or Datadog.

    [:octicons-arrow-right-24: Run lifecycle](operations/runs.md)

</div>

---

## How It Works

![RunAgents architecture diagram showing three-stage request flow: client → platform → external tool](assets/architecture.svg)

Every outbound call from your agent is intercepted, policy-checked, enriched with the correct credentials, and forwarded — all transparently, with no code changes required.

---

## Three Pillars

=== ":material-account-arrow-right: Identity Propagation"

    User identity flows from client → agent → external tool automatically.
    Every downstream service sees **who** made the request, not just which service account.

    - JWT validated at ingress, user ID extracted and forwarded end-to-end
    - Tools receive the real end-user identity on every call
    - Full traceability across the entire request chain

=== ":material-shield-lock: Policy-Driven Access"

    Fine-grained allow/deny rules control which agents can call which tools and at which paths.

    - Policies define resource patterns with allow or deny effects
    - Auto-binding creates policies automatically when you deploy an agent
    - Capability checks enforce operation-level restrictions (e.g. `GET /documents/*` only)

=== ":material-clipboard-check-outline: Just-In-Time Approvals"

    High-risk tools pause the agent until an admin approves. Platform auto-resumes after approval.

    - Admin notified via Slack, PagerDuty, Teams, or Jira
    - Payload hash integrity ensures approved request matches what the agent will send
    - No manual re-triggering — the platform handles the full pause-approve-resume cycle

---

## Ready to Try?

<div class="ra-cta-row">
  <a href="https://try.runagents.io" class="ra-btn-cta">Start Free Trial</a>
  <a href="getting-started/quickstart/" class="ra-btn-outline">Read the Quickstart</a>
</div>

<small>© 2026 RunAgents, Inc. &nbsp;·&nbsp; [Privacy](https://runagents.io/privacy) &nbsp;·&nbsp; [Terms](https://runagents.io/terms)</small>
