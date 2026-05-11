---
title: Approval Connectors
description: Route approval requests to Slack, PagerDuty, Microsoft Teams, or Jira while keeping the decision attached to the same governed run.
---

# Approval connectors

Approval connectors let RunAgents deliver policy-driven approval requests to the systems reviewers already use.

## Supported delivery targets

Current approval delivery targets include:

- Slack
- PagerDuty
- Microsoft Teams
- Jira

## How connectors fit the approval flow

1. A tool call matches a policy rule with `approval_required`.
2. RunAgents creates an approval request and pauses the run.
3. The request is delivered through the configured connector or shown in the UI.
4. The reviewer decision is recorded on the same request and run.
5. If approved, the blocked action resumes automatically.

## Where connectors are configured

Configure connectors in **Settings → Approval Connectors**, then reference connector IDs from policy approval delivery rules.

```yaml
spec:
  approvals:
    - tags: [financial]
      approvers:
        groups: [finance-approvers]
        match: any
      delivery:
        connectors: [slack-finance]
        mode: first_success
        fallbackToUI: true
```

## Go deeper

- [Approvals](../platform/approvals.md)
- [Policy model](../concepts/policy-model.md)
- [Approvals API](../api/approvals.md)
