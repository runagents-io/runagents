# CLI Commands

Complete reference for all `runagents` CLI commands.

All commands support `--output json` (or `-o json`) for machine-readable output.

---

## `runagents config`

Manage CLI configuration.

### `config set`

```bash
runagents config set endpoint <url>
runagents config set api-key <key>
runagents config set namespace <workspace-namespace>
runagents config set assistant-mode <external|runagents|off>
```

| Argument | Description |
|----------|-------------|
| `endpoint` | RunAgents API base URL (e.g., `https://api.runagents.io`) |
| `api-key` | Your API key from the console Settings page |
| `namespace` | Workspace namespace used for API scoping (e.g., `default`) |
| `assistant-mode` | CLI assistant behavior: `external` (default), `runagents` (enable Copilot shell), or `off` |

### `config get`

```bash
runagents config get
```

Displays current configuration with the API key partially masked.

---

## `runagents context`

Export workspace context for external assistants (Codex/Claude Code workflows).

### `context export`

```bash
runagents context export -o json
runagents context export --strict -o json
```

Returns a single snapshot containing:

- agents
- tools
- model providers
- policies
- identity providers
- approval connectors
- approvals
- deploy drafts

Use `--strict` to fail if any resource endpoint is unavailable.

---

## `runagents action`

Validate and apply deterministic action plans (for Codex/Claude Code generated automation).

### `action validate`

```bash
runagents action validate --file plan.json
runagents action validate --file plan.json -o json
```

Performs schema/semantic validation (including `idempotency_key` checks) without mutating resources.

### `action apply`

```bash
runagents action apply --file plan.json
runagents action apply --file plan.json -o json
```

Applies the plan using server-side governance handlers and returns per-action status.

Command alias:

```bash
runagents actions validate --file plan.json
runagents actions apply --file plan.json
```

See [Action Plans](action-plans.md) and [Action Plan Examples](plan-examples.md) for schema and examples.

---

## `runagents copilot`

Natural-language assistant from your terminal.

`runagents copilot` commands are available only when:

```bash
runagents config set assistant-mode runagents
```

### Interactive shell (default)

```bash
runagents
```

Starts Copilot shell when running in a terminal. In non-interactive contexts (CI, pipes), `runagents` prints help instead.

Shell commands:

- `/doctor`
- `/status`
- `/pending`
- `/confirm <action_id>`
- `/reject <action_id>`
- `/reset`
- `/exit`

### Chat command mode

```bash
runagents copilot chat "deploy this folder as billing-agent"
runagents copilot chat --yes "deploy this folder as billing-agent"
```

If the prompt targets `this folder/current folder/repo`, CLI asks for confirmation before uploading local files.  
Use `--yes` to auto-confirm (recommended for scripts/CI).

### Pending/confirm/reject command mode

```bash
runagents copilot pending
runagents copilot confirm act_123
runagents copilot reject act_123
runagents copilot status
runagents copilot status --refresh
runagents copilot doctor
```

### Session reset

```bash
runagents copilot reset-session
```

Project-local continuity files:

- `./.runagents/state.json`
- `./.runagents/memory.md`

---

## `runagents starter-kit`

Seed your account with starter resources for quick experimentation.

```bash
runagents starter-kit
```

Creates:

- **echo-tool** — a built-in echo tool for testing
- **playground-llm** — a model provider configured with OpenAI gpt-4o-mini

Idempotent — safe to run multiple times.

---

## `runagents deploy`

Deploy an agent from source files, a deploy draft, or an existing artifact.

```bash
runagents deploy \
  --name my-agent \
  --file agent.py \
  --file utils.py \
  --tool stripe-api \
  --tool echo-tool \
  --model openai/gpt-4o-mini \
  --policy billing-write-approval \
  --identity-provider google-oidc \
  --requirements-file requirements.txt \
  --entry-point agent.py \
  --framework langgraph
```

Alternative source modes:

```bash
runagents deploy --name billing-agent --draft-id draft_billing_v2 --policy billing-write-approval
runagents deploy --name support-agent --artifact-id art_support_v3 --identity-provider google-oidc
```

| Flag | Description | Required |
|------|-------------|----------|
| `--name` | Agent name (unique identifier) | Yes |
| `--file` | Source file path (repeatable) | One of `--file`, `--draft-id`, or `--artifact-id` |
| `--draft-id` | Existing deploy draft to hydrate from | One of `--file`, `--draft-id`, or `--artifact-id` |
| `--artifact-id` | Existing workflow artifact to deploy | One of `--file`, `--draft-id`, or `--artifact-id` |
| `--tool` | Required tool name (repeatable) | No |
| `--model` | LLM config as `provider/model` | No |
| `--policy` | Policy name to bind during deploy (repeatable) | No |
| `--identity-provider` | Identity provider to bind during deploy | No |
| `--requirements-file` | Requirements file to include with source deploys | No |
| `--entry-point` | Entrypoint file or module for source deploys | No |
| `--framework` | Framework hint for source deploys | No |

The deploy command:

1. Validates exactly one deploy source (`--file`, `--draft-id`, or `--artifact-id`)
2. Uploads source files or references the existing draft or artifact
3. Attaches tools, models, policies, and optional identity provider bindings
4. Reports deployment status and build metadata when present

**Example output:**

```
Agent "my-agent" deployed successfully.
Agent: my-agent
Build ID: build-a1b2c3
Tools created: [stripe-api]
```

---

## `runagents catalog`

Discover, inspect, initialize, and deploy agents from the RunAgents catalog.

### `catalog list`

```bash
runagents catalog list
runagents catalog list --search google --integration calendar
runagents catalog list --category "Enterprise Productivity" --tag Gmail
```

Useful filters:

- `--search`
- `--category`
- `--tag`
- `--integration`
- `--governance`
- `--page`
- `--page-size`

### `catalog show`

```bash
runagents catalog show google-workspace-assistant-agent
runagents catalog show google-workspace-assistant-agent --version 1.2.0
```

Shows the deployment-ready manifest, including:

- summary and governance traits
- required integrations
- required and recommended tools
- source file list
- default identity provider and policy hints

### `catalog versions`

```bash
runagents catalog versions google-workspace-assistant-agent
```

Lists published versions in descending semantic-version order.

### `catalog init`

```bash
runagents catalog init google-workspace-assistant-agent
runagents catalog init google-workspace-assistant-agent ./workspace-assistant
runagents catalog init google-workspace-assistant-agent ./workspace-assistant --force
```

Writes the catalog source files locally and saves the fetched manifest as `runagents.catalog.json`.

### `catalog deploy`

```bash
runagents catalog deploy google-workspace-assistant-agent
runagents catalog deploy google-workspace-assistant-agent \
  --name workspace-assistant \
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

Useful flags:

| Flag | Description |
|------|-------------|
| `--version` | Deploy a specific catalog version |
| `--name` | Override the deployed agent name |
| `--tool` | Override required tool names |
| `--model` | Override the suggested model as `provider/model` |
| `--policy` | Attach policies during deploy |
| `--identity-provider` | Override the identity provider |
| `--dry-run` | Print the deploy payload instead of sending it |

If the catalog manifest contains a bare `defaultModel` such as `gpt-4.1`, `catalog deploy` treats it as `openai/gpt-4.1` unless you pass `--model`.

---

## `runagents policies`

Manage policy rules and approval routing.

### `policies list`

```bash
runagents policies list
```

Lists policies with rule count, approval count, readiness, and bound-agent usage.

### `policies get`

```bash
runagents policies get workspace-write-approval
```

Shows the full policy shape plus which deployed agents are currently bound to it.

### `policies apply`

```bash
runagents policies apply -f policy.yaml
runagents policies apply -f policy.yaml --name workspace-write-approval
```

Accepts either:

- a full request document with `name` and `spec`
- or a raw `spec` document when `--name` is supplied

Both YAML and JSON are supported.

### `policies delete`

```bash
runagents policies delete workspace-write-approval
```

### `policies translate`

```bash
runagents policies translate --from "Allow Google Workspace reads and require approval for writes"
```

Returns structured policy rules suitable for review before applying.

---

## `runagents agents`

Manage agents.

### `agents list`

```bash
runagents agents list
```

```
NAME          STATUS    IMAGE
hello-world   Running   registry.runagents.io/hello-world:abc123
my-agent      Pending   registry.runagents.io/my-agent:def456
```

### `agents get`

```bash
runagents agents get <namespace> <name>
```

Displays full agent details including configuration, required tools, LLM config, and status.

### `agents delete`

```bash
runagents agents delete <namespace> <name>
```

!!! warning
    Deleting an agent removes the live deployment. Historical run data may still be retained for audit depending on platform configuration.

---

## `runagents tools`

Manage tools.

### `tools list`

```bash
runagents tools list
```

```
NAME          TOPOLOGY   BASE URL                     ACCESS       STATUS
echo-tool     Internal   http://governance.agent-system.svc:8092   Restricted   Available
stripe-api    External   https://api.stripe.com        Restricted   Available
google-drive  External   https://www.googleapis.com    Restricted   Available
```

### `tools get`

```bash
runagents tools get <name>
```

Displays full tool details including connection, authentication, governance, and capabilities.

### `tools create`

```bash
runagents tools create --file tool.json
```

Create a tool from a JSON definition file. See [Tools API](../api/tools.md) for the schema.

**Example `tool.json`:**

```json
{
  "name": "stripe-api",
  "description": "Stripe payments API",
  "connection": {
    "topology": "External",
    "baseUrl": "https://api.stripe.com",
    "port": 443,
    "scheme": "HTTPS",
    "authentication": {
      "type": "APIKey",
      "apiKeyConfig": {
        "in": "Header",
        "name": "Authorization",
        "valuePrefix": "Bearer ",
        "secretRef": {"name": "stripe-key"}
      }
    }
  },
  "governance": {
    "accessControl": {"mode": "Restricted"}
  }
}
```

### `tools delete`

```bash
runagents tools delete <name>
```

---

## `runagents models`

Manage model providers.

### `models list`

```bash
runagents models list
```

```
NAME              PROVIDER   MODELS                     STATUS
playground-llm    openai     gpt-4o-mini                Available
production-llm    anthropic  claude-sonnet-4-20250514    Available
bedrock-llm       bedrock    anthropic.claude-opus-4-6-v1 Available
```

### `models get`

```bash
runagents models get <name>
```

### `models create`

```bash
runagents models create --file provider.json
```

**Example `provider.json`:**

```json
{
  "name": "production-llm",
  "provider": "openai",
  "endpoint": "https://api.openai.com",
  "models": ["gpt-4o", "gpt-4o-mini"],
  "auth": {
    "type": "APIKey",
    "apiKeyConfig": {
      "in": "Header",
      "name": "Authorization",
      "valuePrefix": "Bearer ",
      "secretRef": {"name": "openai-key"}
    }
  }
}
```

### `models delete`

```bash
runagents models delete <name>
```

---

## `runagents identity-providers`

Manage end-user identity providers for authenticated agent access.

### `identity-providers list`

```bash
runagents identity-providers list
```

Lists identity providers configured in the current workspace.

### `identity-providers get`

```bash
runagents identity-providers get google-oidc
```

Shows the configured host, issuer, JWKS URI, user claim, audiences, and allowed domains.

### `identity-providers apply`

```bash
runagents identity-providers apply -f google-oidc.yaml
runagents identity-providers apply -f raw-spec.yaml --name google-oidc
```

Creates or updates an identity provider from YAML or JSON.

Example `google-oidc.yaml`:

```yaml
name: google-oidc
spec:
  host: portal.example.com
  identityProvider:
    issuer: https://accounts.google.com
    jwksUri: https://www.googleapis.com/oauth2/v3/certs
    audiences:
      - portal.example.com
  userIDClaim: email
  allowedDomains:
    - example.com
```

`apply` accepts:

- a full identity provider document with `name` and `spec`
- or a raw `spec` document when you also pass `--name`

### `identity-providers delete`

```bash
runagents identity-providers delete google-oidc
```

Deletes the identity provider from the current workspace.

---

## `runagents runs`

View and manage agent runs.

### `runs list`

```bash
runagents runs list
runagents runs list --agent hello-world
runagents runs list --status PAUSED_APPROVAL --user alice@example.com --limit 25
```

```
ID                       AGENT         USER               STATUS            UPDATED
01HQXYZ1234567890ABCDEF  hello-world   alice@example.com COMPLETED         2026-02-23T10:15:00Z
01HQXYZ1234567890ABCDEG  my-agent      alice@example.com RUNNING           2026-02-23T10:20:00Z
01HQXYZ1234567890ABCDEH  my-agent      bob@example.com   PAUSED_APPROVAL   2026-02-23T10:22:00Z
```

| Flag | Description |
|------|-------------|
| `--agent` | Filter by agent name |
| `--status` | Filter by status |
| `--user` | Filter by user ID |
| `--conversation` | Filter by conversation ID |
| `--limit` | Maximum number of runs to show (`0` for all) |

### `runs get`

```bash
runagents runs get <run-id>
```

Displays run details including namespace, user, blocked action, timestamps, and the initial message when present.

### `runs events`

```bash
runagents runs events <run-id>
runagents runs events <run-id> --type APPROVAL_REQUIRED --limit 20
```

```
SEQ  TYPE               ACTOR               DETAIL                                                   TIMESTAMP
12   TOOL_REQUEST       workspace-agent     Called calendar POST https://www.googleapis.com/...      2026-04-09T15:10:03Z
13   APPROVAL_REQUIRED  governance          Approval required for calendar (create-event)            2026-04-09T15:10:03Z
14   APPROVED           admin@company.com   Approved by admin@company.com                            2026-04-09T15:12:40Z
15   RESUMED            governance          Run resumed after external decision                      2026-04-09T15:12:41Z
16   COMPLETED          workspace-agent     Run completed successfully                               2026-04-09T15:12:43Z
```

Useful flags:

- `--type`
- `--limit`

### `runs timeline`

```bash
runagents runs timeline <run-id>
```

Builds an operator timeline from the run plus its ordered events. This is the quickest way to understand whether a run is blocked on approval, blocked on consent, resumed, or failed.

### `runs wait`

```bash
runagents runs wait <run-id>
runagents runs wait <run-id> --timeout 10m --interval 5s
```

Polls the run until it reaches a terminal state (`COMPLETED` or `FAILED`) and then prints the final run record.

### `runs export`

```bash
runagents runs export <run-id>
runagents runs export <run-id> -o json
```

Exports one JSON payload containing:

- the run
- the ordered event list
- the derived operator timeline

---

## `runagents approvals`

Manage access requests and approvals.

### `approvals list`

```bash
runagents approvals list
```

```
ID                       AGENT         TOOL          STATUS     CREATED
01HQXYZ1234567890ABCDEF  my-agent      stripe-api    Pending    2026-02-23 10:22:00
01HQXYZ1234567890ABCDEG  data-agent    google-drive  Provisioned 2026-02-23 09:15:00
```

### `approvals approve`

```bash
runagents approvals approve <request-id>
runagents approvals approve <request-id> --scope once
runagents approvals approve <request-id> --scope run
runagents approvals approve <request-id> --scope window --duration 4h
```

Approves the access request with an optional explicit scope:

- `--scope once` for a single blocked action
- `--scope run` for the current run only
- `--scope window --duration 1h|4h|24h` for a time-bound user/agent/tool window

If you provide `--duration` without `--scope`, the CLI treats it as a time window approval.

### `approvals reject`

```bash
runagents approvals reject <request-id>
```

---

## `runagents approval-connectors`

Manage approval delivery connectors, workspace defaults, and connector activity.

### `approval-connectors list`

```bash
runagents approval-connectors list
```

Lists approval connectors configured in the current workspace.

### `approval-connectors get`

```bash
runagents approval-connectors get <connector-id>
```

Shows the connector type, endpoint, timeout, security mode, and configured headers.

### `approval-connectors apply`

```bash
runagents approval-connectors apply -f connector.yaml
```

Creates or updates a connector from YAML or JSON.

Example `connector.yaml`:

```yaml
name: secops-slack
type: slack
endpoint: C0123456789
headers:
  X-Slack-Bot-Token: xoxb-...
timeout_seconds: 15
slack_security_mode: compat
```

If the file matches an existing connector by `id` or `name`, the CLI updates it. Otherwise it creates a new connector.

### `approval-connectors delete`

```bash
runagents approval-connectors delete <connector-id>
```

Deletes the connector from the current workspace.

### `approval-connectors test`

```bash
runagents approval-connectors test <connector-id>
```

Replays the connector's current configuration through the approval connector test API and prints configuration, credentials, and connectivity checks.

### `approval-connectors defaults get`

```bash
runagents approval-connectors defaults get
```

Shows the workspace defaults used when approval policies do not explicitly set connector delivery behavior.

### `approval-connectors defaults set`

```bash
runagents approval-connectors defaults set --delivery-mode first_success --fallback-to-ui=true --timeout-seconds 20
```

Supported flags:

- `--delivery-mode`
- `--fallback-to-ui`
- `--timeout-seconds`

### `approval-connectors activity`

```bash
runagents approval-connectors activity
runagents approval-connectors activity --limit 100
```

Displays recent connector delivery events, including dispatch outcome, HTTP result, approval request correlation, and operator-facing messages.

---

## `runagents analyze`

Analyze source files to detect tools, models, secrets, and dependencies.

```bash
runagents analyze --file agent.py
```

```
Analysis Results:
─────────────────
Entry Point:    agent.py
Requirements:   openai>=1.0, requests

Detected Tools:
  - stripe-api (https://api.stripe.com) [agent.py:15]
  - slack-api (https://slack.com/api) [agent.py:28]

Model Usages:
  - openai/gpt-4o (role: default) [agent.py:3]

Secrets Found:
  ⚠ Possible API key [agent.py:8] (severity: high)

Outbound Destinations:
  - api.stripe.com
  - slack.com
  - api.openai.com
```

| Flag | Description |
|------|-------------|
| `--file` | Source file path (repeatable) |

!!! warning "Secret Detection"
    The analyzer checks for hardcoded secrets using regex patterns and Shannon entropy analysis. Remove any secrets from your code before deploying.

---

## Global Flags

These flags work with any command:

| Flag | Short | Description |
|------|-------|-------------|
| `--endpoint` | | Override the configured API endpoint |
| `--api-key` | | Override the configured API key |
| `--output` | `-o` | Output format: `table` (default) or `json` |
| `--help` | `-h` | Show help for any command |
| `--version` | `-v` | Alias for `runagents version` |

---

## JSON Output

All list and get commands support `--output json` for scripting:

```bash
runagents agents list -o json | jq '.[].name'
```

```json
"hello-world"
"my-agent"
```

---

!!! tip "Need help?"
    Run `runagents <command> --help` for usage details on any command, or contact us at [try@runagents.io](mailto:try@runagents.io).
