---
title: Pricing
description: Simple, transparent pricing for RunAgents. Start free, scale with usage, or self-host for full control.
---

# Pricing

RunAgents offers straightforward, usage-based pricing. Start with a free trial -- no credit card required -- and upgrade when you are ready.

---

## Plans

| | **Free Trial** | **Pro** | **Self-Hosted** |
|---|---|---|---|
| **Price** | $0 | $24/month | Contact us |
| **Duration** | 30 days | Ongoing | Ongoing |
| **Actions per month** | 1,000 | 50,000 | Unlimited |
| **Agents** | Unlimited | Unlimited | Unlimited |
| **Tools** | Unlimited | Unlimited | Unlimited |
| **Model providers** | Unlimited | Unlimited | Unlimited |
| **Identity propagation** | Included | Included | Included |
| **Policy engine** | Included | Included | Included |
| **Just-in-time approvals** | Included | Included | Included |
| **OAuth consent flows** | Included | Included | Included |
| **Support** | Community | Email | Dedicated |

!!! tip "Promo: 3 months free on Pro"

    Add a payment method during your free trial and get **3 months of Pro for free** -- 1,000 actions/month included. After the promo period ends, your plan transitions to the standard Pro tier at $24/month with 50,000 actions/month.

---

## What Counts as an Action?

An **action** is a single agent-to-tool API call intercepted by the RunAgents platform. Every time your agent makes an outbound request to a registered tool, that counts as one action.

**Examples:**

- Your agent calls the Stripe API to create a charge -- **1 action**
- Your agent reads a Google Drive file, then updates a Notion page -- **2 actions**
- Your agent calls your LLM gateway for model inference -- **not an action** (LLM calls are not metered)
- Your agent makes 3 tool calls in a single run -- **3 actions**

!!! info "Only tool calls are metered"

    LLM gateway requests, agent invocations, and console usage do not count toward your action limit. You are only charged for outbound calls from agents to registered tools.

---

## Grace Period

When your free trial expires or you exhaust your monthly action limit, your workspace enters a **read-only grace period** of 30 days. During this time:

- You can view agents, tools, runs, and configuration in the console
- Agents cannot make new tool calls
- No data is deleted

Upgrade to Pro at any time to restore full access.

---

## Frequently Asked Questions

### Do I need a credit card to start?

No. The free trial gives you 30 days and 1,000 actions with no payment method required. Add a card when you are ready to continue.

### What happens if I exceed my action limit mid-month?

Your agents enter read-only mode for the remainder of the billing period. Existing runs are preserved, but new tool calls are blocked until the next billing cycle or until you upgrade your plan.

### Can I monitor my usage?

Yes. The console dashboard displays your current action count and remaining quota. You can also query usage via the API.

### Is there an enterprise plan?

For teams that need higher limits, SLAs, or dedicated infrastructure, contact us at [try@runagents.io](mailto:try@runagents.io?subject=Enterprise Pricing) to discuss a custom plan.

### Can I self-host RunAgents?

Yes. RunAgents can be deployed to your own Kubernetes cluster -- your cloud account, on-premise, or air-gapped. Self-hosted deployments have no action limits. See the [Self-Hosted Deployment Guide](self-hosted/deployment.md) or [contact us](mailto:try@runagents.io?subject=Self-Hosted RunAgents) to get started.

---

## Get Started

!!! tip "Start your free trial"

    Deploy agents, register tools, and see the full security model in action -- no credit card required.

    [:material-rocket-launch: Start Free Trial](https://try.runagents.io){ .md-button .md-button--primary }
    [:material-email-outline: Contact Sales](mailto:try@runagents.io?subject=RunAgents Pricing){ .md-button }
