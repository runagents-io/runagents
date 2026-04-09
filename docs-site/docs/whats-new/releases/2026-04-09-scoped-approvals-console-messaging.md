# Release Notes: Scoped Approvals, Clearer Operations, and Better Messaging Workflows

_April 9, 2026_

This release makes RunAgents easier to operate in production when your agents need to:

- read from external systems freely but gate writes behind approval
- act on behalf of end users through OAuth-connected tools such as Google Workspace
- pause for approval or consent and resume without manual intervention
- complete work from conversational surfaces such as WhatsApp and return the final result to the same thread

The biggest improvements in this release are:

- **Scoped approvals** so teams can approve one action, one run, or a short-lived work window
- **More reliable pause and resume behavior** for approval- and consent-gated runs
- **A clearer operations console** that separates approval work from consent work and makes runs easier to follow from the agent view
- **Google Workspace calendar writes under policy control** for the Google Workspace assistant
- **Stronger messaging-surface continuity** so resumed runs are more likely to complete back in the original conversation
- **A new public RunAgents skills library** for Codex, Claude Code, Cursor, and similar assistants

## Who should care

This release is especially relevant if you are running:

- approval-gated writes against sensitive systems
- delegated-user OAuth tools such as Google Workspace
- customer-facing agents on chat, messaging, or support channels
- multi-agent workspaces where operators need a clearer view of pending work
- assistant-driven deployment and operations workflows from tools such as Codex, Claude Code, and Cursor

## What’s New

### Scoped approvals for governed writes

RunAgents now supports approval scopes that better match how real teams work.

When a policy returns `approval_required`, operators can approve:

- **Once**: approve one exact blocked action
- **This run**: approve matching actions for the current run
- **For a limited window**: approve matching actions for the same user, agent, and tool for a short period of time

Why this matters:

- sensitive writes can stay tightly controlled
- retries inside the same run no longer require repeated approvals
- teams can support short working sessions without broadening policy permanently

Approval behavior remains policy-driven. Policies still define whether a call is allowed, denied, or requires approval. Approval scopes simply make the runtime approval outcome more useful and more predictable.

### More reliable run pause and resume behavior

This release improves the full lifecycle of governed runs:

- approval-gated runs resume more reliably after approval
- consent-gated runs resume more reliably after OAuth completion
- resumed tool results are delivered back to the requesting surface more consistently

This reduces manual retrying and makes it easier to trust long-running governed workflows.

### A clearer console for operators

The console is now more explicit about what kind of intervention is required.

Highlights include:

- a more agent-centric run experience
- clearer separation between approval-related work and consent-related work
- better distinction between current deployment runs and historical runs
- cleaner active queues by hiding stale deleted-agent approval entries
- approval scope selection directly from the console workflow

The practical benefit is simple: operators can understand what is blocked, who needs to act, and what will happen after approval with less guesswork.

### Google Workspace assistant improvements

The Google Workspace assistant now supports explicit Google Calendar event creation for clear scheduling requests while keeping writes inside RunAgents governance.

That means teams can use a single Google-first assistant across:

- Gmail
- Calendar
- Drive
- Docs
- Sheets
- Tasks
- Keep

while still preserving:

- policy enforcement
- approval gates for writes
- OAuth consent for delegated-user access
- auditability across pause and resume boundaries

### Better messaging-surface continuity

This release also improves how governed runs behave on messaging surfaces such as WhatsApp.

RunAgents continues to manage:

- execution
- identity propagation
- approvals
- consent
- run state
- audit

while the messaging surface remains responsible for:

- inbound message delivery
- thread routing
- channel-specific interaction behavior
- user-to-workspace identity linking

The result is a smoother user experience when a request pauses for approval or consent and then resumes back into the same conversation.

### A public skills library for external assistants

This release also adds a first-party public skills library for AI coding assistants working with RunAgents.

These skills are designed as reusable workflow packs rather than one-off prompt snippets. They are written to be external-facing, so customers and partners can use them across their own environments without depending on private internal setup.

The library now covers:

- **Build** workflows such as agent authoring and action-plan-driven changes
- **Wire** workflows such as catalog deployment, tool onboarding, identity providers, and model providers
- **Govern** workflows such as approval policy design and OAuth consent debugging
- **Operate** workflows such as run debugging and observability triage
- **Interface** workflows for web apps, WhatsApp, Slack, internal portals, and other surfaces
- **Connector** workflows for policy, approval, and observability integrations with external systems

It is designed to work well with:

- Codex and skill-native environments
- Claude Code through `CLAUDE.md` imports or project slash commands
- Cursor and other assistants through project rules and shared workflow files

This makes the assistant story more production-ready. Teams can give their coding assistants reusable RunAgents operating workflows instead of repeating the same context and guidance in every prompt.

## What You Can Do With This Release

### Run approval-gated writes with less friction

A common production pattern is:

- reads are allowed
- writes require approval

With this release, that workflow is more practical:

1. a run attempts a governed write
2. policy returns `approval_required`
3. the run pauses and creates an approval request
4. an operator approves once, for the run, or for a short window
5. the run resumes automatically
6. the write proceeds if policy, capability, and consent requirements are satisfied

### Build delegated-user Google workflows

If your tools use OAuth2 and delegated-user tokens, this release makes the combination of:

- consent
- approval
- resumed execution

much more predictable.

That is especially useful for workflows such as:

- creating a calendar event after the user approves the write
- reading a user’s mailbox, files, or tasks after consent
- continuing the same run after the user completes Google authorization

### Operate from the surfaces you already use

This release does not require teams to adopt a new operator workflow.

The public CLI, SDK, and API remain the main external surfaces for deploying agents, inspecting runs, and handling approvals. The release improves the runtime behavior behind those interfaces without forcing customers to relearn the platform.

### Standardize assistant-driven workflows

If you deploy and operate RunAgents through AI coding assistants, this release now gives you a public skills library that can be reused across projects.

That means teams can standardize workflows such as:

- deploying the Google Workspace assistant from the catalog
- registering tools with the right capabilities and OAuth scopes
- designing approval-required policies for sensitive writes
- tracing paused, resumed, and failed runs
- wiring RunAgents behind user-facing surfaces such as WhatsApp or Slack

The result is less prompt churn, more consistent operator behavior, and a better path from experimentation to production.

## Public CLI Commands You Can Use Today

The CLI remains the fastest way to configure a workspace, deploy agents, inspect runs, and handle approvals.

### Install and configure

```bash
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
runagents version

runagents config set endpoint https://your-workspace.try.runagents.io
runagents config set api-key ra_ws_your_workspace_key
runagents config set namespace default
runagents config get
```

### Seed starter resources

```bash
runagents starter-kit
```

### Analyze source before deploy

```bash
runagents analyze --file agent.py
```

### Deploy an agent

```bash
runagents deploy \
  --name hello-world \
  --file agent.py \
  --tool echo-tool \
  --model openai/gpt-4o-mini
```

### Inspect agents and runs

```bash
runagents agents list
runagents agents get default hello-world

runagents runs list --agent hello-world
runagents runs get <run-id>
runagents runs events <run-id>
```

### Handle approvals

```bash
runagents approvals list
runagents approvals approve <request-id>
runagents approvals reject <request-id>
```

### Export workspace context

```bash
runagents context export -o json
```

### Use the public skills library

The public skills library is documented here:

```text
https://docs.runagents.io/cli/skills/
https://github.com/runagents-io/runagents/tree/main/skills
```

For Codex-style skill folders:

```bash
git clone https://github.com/runagents-io/runagents.git
mkdir -p ~/.codex/skills
cp -R runagents/skills/runagents-approval-policy ~/.codex/skills/
```

For Claude Code, the same skills can be imported into `CLAUDE.md` or wrapped as project slash commands under `.claude/commands/`.

## Public Python SDK Examples

The Python SDK remains the primary programmatic path for teams deploying agents or integrating RunAgents into Python-based workflows.

### Install

```bash
pip install runagents
pip install runagents[mcp]
pip install runagents[dev]
```

### Configure

```bash
runagents config set endpoint https://YOUR_WORKSPACE.try.runagents.io
runagents config set api-key ra_ws_YOUR_KEY
runagents config set namespace default
```

Or via environment variables:

```bash
export RUNAGENTS_ENDPOINT=https://YOUR_WORKSPACE.try.runagents.io
export RUNAGENTS_API_KEY=ra_ws_YOUR_KEY
export RUNAGENTS_NAMESPACE=default
```

### Manage platform resources from Python

```python
from runagents import Client

client = Client()

agents = client.agents.list()
for agent in agents:
    print(agent.name, agent.namespace, agent.status)

runs = client.runs.list(agent="payment-agent", limit=10)
for run in runs:
    print(run.id, run.status, run.created_at)

approvals = client.approvals.list()
client.approvals.approve("req-abc123")
client.approvals.reject("req-abc123")
```

### Deploy an agent from source files

```python
from runagents import Client

client = Client()

result = client.agents.deploy(
    name="payment-agent",
    source_files={"agent.py": open("agent.py").read()},
    system_prompt="You are a payment assistant.",
    required_tools=["stripe-api"],
    llm_configs=[{"provider": "openai", "model": "gpt-4o-mini", "role": "default"}],
    requirements="runagents>=0.2.0\n",
    entry_point="agent.py",
)
print(result.status)
```

### Write agent code with the SDK

```python
from runagents import Agent

agent = Agent()

response = agent.chat(message="Summarize this order")
print(response["choices"][0]["message"]["content"])

result = agent.call_tool(
    name="stripe-api",
    path="/v1/charges",
    payload={"amount": 1000, "currency": "usd"},
)
```

## Public API Commands You Can Use Today

The public API remains the main customer-facing surface for deployment, approval handling, tool registration, and run inspection.

Base URL:

```bash
export API="https://api.runagents.io"
export RUNAGENTS_API_KEY="ra_ws_your_workspace_key"
```

### Seed starter resources

```bash
curl -X POST "$API/api/starter-kit" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json"
```

### Create a policy

```bash
curl -X POST "$API/api/policies" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-echo-policy",
    "spec": {
      "policies": [
        {
          "permission": "allow",
          "resource": "http://governance.agent-system.svc:8092/*",
          "operations": ["GET", "POST"]
        }
      ]
    }
  }'
```

### Deploy an agent

```bash
curl -X POST "$API/api/deploy" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "hello-world",
    "source_files": {
      "agent.py": "def handler(request):\n    return {\"response\": \"hello from runagents\"}"
    },
    "entry_point": "agent.py",
    "required_tools": ["echo-tool"],
    "llm_configs": [
      {"provider": "openai", "model": "gpt-4o-mini", "role": "chat"}
    ],
    "policies": ["hello-echo-policy"]
  }'
```

### List agents

```bash
curl https://api.runagents.io/api/agents \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY"
```

### Invoke an agent

```bash
curl -X POST https://api.runagents.io/api/agents/agent-system/payment-agent/invoke \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the recent charges?"}'
```

### Create and inspect runs

```bash
curl -X POST https://api.runagents.io/runs \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "payment-agent",
    "user_id": "user@example.com",
    "conversation_id": "conv-abc123",
    "namespace": "agent-system"
  }'

curl "https://api.runagents.io/runs?agent_id=payment-agent" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY"

curl https://api.runagents.io/runs/<run-id> \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY"

curl https://api.runagents.io/runs/<run-id>/events \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY"
```

### Handle approvals through the public API

```bash
curl "$API/governance/requests?status=PENDING" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY"

curl -X POST "$API/governance/requests/<request-id>/approve" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'

curl -X POST "$API/governance/requests/<request-id>/reject" \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Not approved for production writes"}'
```

### Register an OAuth2 tool

For delegated-user tools such as Google Workspace, the Tools API remains the public registration surface:

```bash
curl -X POST https://api.runagents.io/api/tools \
  -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "google-drive",
    "spec": {
      "description": "Google Drive file management",
      "connection": {
        "topology": "External",
        "baseUrl": "https://www.googleapis.com",
        "port": 443,
        "scheme": "HTTPS",
        "authentication": {
          "type": "OAuth2",
          "oauth2Config": {
            "authUrl": "https://accounts.google.com/o/oauth2/v2/auth",
            "tokenUrl": "https://oauth2.googleapis.com/token",
            "scopes": ["https://www.googleapis.com/auth/drive.readonly"]
          }
        }
      },
      "governance": {
        "accessControl": {
          "mode": "Restricted"
        }
      },
      "capabilities": [
        {
          "name": "list-files",
          "method": "GET",
          "path": "/drive/v3/files",
          "description": "List files in Google Drive"
        }
      ],
      "riskTags": ["pii"]
    },
    "credentials": {
      "client_id": "123456789.apps.googleusercontent.com",
      "client_secret": "GOCSPX-..."
    }
  }'
```

### Deploying the Google Workspace assistant

This release also makes the Google Workspace assistant more useful for teams that want one agent to work across Gmail, Calendar, Drive, Docs, Sheets, Tasks, and Keep.

```bash
cd catalog/agents/google-workspace-assistant

runagents deploy \
  --name google-workspace-assistant-agent \
  --file src/agent.py \
  --tool email \
  --tool calendar \
  --tool drive \
  --tool docs \
  --tool sheets \
  --tool tasks \
  --tool keep \
  --model openai/gpt-4.1
```

This catalog blueprint now includes explicit calendar event creation while still routing writes through policy and approval.

## Upgrade Notes

### Existing environments may need a one-time approval-grant bootstrap

If you are upgrading a long-lived environment, make sure the approval-grant backing store is provisioned before relying on scoped approval behavior.

For some existing environments, this may require a one-time datastore bootstrap for approval grants.

### Policies remain the source of truth

Approval behavior is still policy-driven.

Continue to model access with policies and bindings using rules such as:

- `allow`
- `deny`
- `approval_required`

Tool-level approval flags remain legacy metadata and should not be treated as the primary runtime authorization mechanism.

### Consent still matters for delegated-user writes

If you want users to perform governed writes against delegated-user tools such as Google Workspace, make sure the tool has the OAuth scopes required for the operations you want to support.

A write-capable tool definition still needs a matching write-capable token grant from the user.

### No breaking changes to the public surfaces in this release

The public CLI, SDK, and API entry points remain the same in this release.

The main changes are in runtime behavior, operator experience, approval scope semantics, and the new public skills library for assistant-driven workflows.

## Recommended Next Steps

After upgrading, we recommend:

1. review sensitive write policies and decide where one-time, run-level, or short-window approvals are appropriate
2. test one approval-gated write workflow end to end from the surface your users actually use
3. verify OAuth-backed tools have the scopes required for the operations you want to support
4. update any internal runbooks that still describe approvals as temporary policy-binding workflows
5. if you use Codex, Claude Code, Cursor, or similar tools, adopt the public RunAgents skills library for repeatable deployment and operations workflows

## Summary

This release makes RunAgents meaningfully more production-ready for teams building governed, customer-facing agent workflows.

It gives teams:

- more practical approvals
- stronger pause and resume behavior
- a clearer operations experience
- better Google Workspace support
- more reliable messaging-surface workflows
- a stronger public assistant workflow story through the new skills library

without forcing changes to the public CLI, SDK, or API patterns customers already use today.
