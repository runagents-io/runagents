# CLI v1.2.0: Governance and Operations from the Terminal

RunAgents CLI `v1.2.0` turns the terminal into a first-class operations surface for governed agents.

This release closes the gap between the public platform story and what customers can actually do from the CLI. You can now discover catalog agents, manage policies and identity providers, configure approval connectors, inspect runs in more depth, and deploy agents with governance bindings directly from the terminal.

---

## Highlights

### Catalog-first deployment workflows

Start from maintained blueprints instead of scaffolding every workflow by hand.

```bash
runagents catalog list
runagents catalog show google-workspace-assistant-agent
runagents catalog deploy google-workspace-assistant-agent \
  --name google-workspace-assistant-agent \
  --tool email \
  --tool calendar \
  --tool drive \
  --tool docs \
  --tool sheets \
  --tool tasks \
  --tool keep \
  --policy workspace-write-approval \
  --identity-provider google-oidc
```

This is the fastest way to stand up production-shaped assistants with real policy, approval, and OAuth behavior.

### Governance resources are now first-class CLI objects

You no longer need to fall back to the console or raw API calls for core governance setup.

Available command families now include:

- `runagents policies`
- `runagents approval-connectors`
- `runagents identity-providers`
- scoped `runagents approvals approve`

Example:

```bash
runagents policies apply -f workspace-write-approval.yaml
runagents approval-connectors apply -f secops-slack.yaml
runagents identity-providers apply -f google-oidc.yaml
runagents approvals approve req_123 --scope run
```

### Richer run debugging and operator workflows

Run inspection now goes beyond basic listing.

```bash
runagents runs list --agent google-workspace-assistant-agent --status PAUSED_APPROVAL
runagents runs timeline <run-id>
runagents runs wait <run-id> --timeout 5m
runagents runs export <run-id> -o json
```

This makes it much easier to debug approvals, consent pauses, resumed execution, and end-to-end tool behavior from the terminal.

### Deploy from the terminal with real governance bindings

Top-level deploy now supports the fields customers expect for production rollout.

```bash
runagents deploy \
  --name billing-agent \
  --file agent.py \
  --tool stripe-api \
  --model openai/gpt-4o-mini \
  --policy billing-write-approval \
  --identity-provider google-oidc \
  --requirements-file requirements.txt \
  --entry-point agent.py \
  --framework langgraph
```

You can also deploy from existing drafts or workflow artifacts:

```bash
runagents deploy --name billing-agent --draft-id draft_billing_v2
runagents deploy --name billing-agent --artifact-id art_billing_v2
```

### Better external assistant context

`runagents context export` now includes the governance and identity resources external assistants need to generate accurate plans.

Exported context now includes:

- agents
- tools
- model providers
- policies
- identity providers
- approval connectors
- approvals
- deploy drafts

This improves Claude Code, Codex, Cursor, and similar assistant workflows by reducing missing-context drift.

---

## Why this release matters

`v1.2.0` makes the CLI viable as a serious control plane for day-to-day operator work, not just a convenience wrapper around deploy.

That means teams can:

- bootstrap real assistants from the catalog
- manage governance resources from the terminal
- hand richer context to external coding assistants
- debug approval-heavy workflows without switching surfaces

---

## Upgrade notes

- `v1.1.2` remains the immediate upgrade target if you only need the deploy payload compatibility fix
- move to `v1.2.0` when you want the full governance-and-operations CLI surface
- no migration is required for existing agents, but your local install path should be updated to the latest release

Install paths:

```bash
pip install -U runagents
npm install -g @runagents/cli
brew upgrade runagents
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
```

---

## Related docs

- [CLI Commands](../../cli/commands.md)
- [Agent Catalog](../../platform/agent-catalog.md)
- [Policies API](../../api/policies.md)
- [Approval Connectors API](../../api/approval-connectors.md)
- [Identity Providers](../../platform/identity-providers.md)
- [Run Lifecycle](../../operations/runs.md)
