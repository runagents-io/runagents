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
```

| Argument | Description |
|----------|-------------|
| `endpoint` | RunAgents API base URL (e.g., `https://api.runagents.io`) |
| `api-key` | Your API key from the console Settings page |

### `config get`

```bash
runagents config get
```

Displays current configuration with the API key partially masked.

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

Deploy an agent from source files.

```bash
runagents deploy \
  --name my-agent \
  --file agent.py \
  --file utils.py \
  --tool stripe-api \
  --tool echo-tool \
  --model openai/gpt-4o-mini
```

| Flag | Description | Required |
|------|-------------|----------|
| `--name` | Agent name (unique identifier) | Yes |
| `--file` | Source file path (repeatable) | Yes |
| `--tool` | Required tool name (repeatable) | No |
| `--model` | LLM config as `provider/model` | No |

The deploy command:

1. Reads the specified source files
2. Sends them to the platform for analysis
3. Creates the agent with the specified tool and model bindings
4. Reports deployment status

**Example output:**

```
Deploying agent "my-agent"...
✓ Agent deployed successfully

Name:    my-agent
Status:  Pending
Tools:   stripe-api, echo-tool
Model:   openai/gpt-4o-mini
```

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
    Deleting an agent removes its deployment and all associated resources. Active runs will be terminated.

---

## `runagents tools`

Manage tools.

### `tools list`

```bash
runagents tools list
```

```
NAME          TOPOLOGY   BASE URL                     ACCESS       STATUS
echo-tool     Internal   http://governance:8092/echo   Open         Available
stripe-api    External   https://api.stripe.com        Restricted   Available
google-drive  External   https://www.googleapis.com    Critical     Available
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

## `runagents runs`

View and manage agent runs.

### `runs list`

```bash
runagents runs list
runagents runs list --agent hello-world
```

```
ID                       AGENT         STATUS            CREATED
01HQXYZ1234567890ABCDEF  hello-world   COMPLETED         2026-02-23 10:15:00
01HQXYZ1234567890ABCDEG  my-agent      RUNNING           2026-02-23 10:20:00
01HQXYZ1234567890ABCDEH  my-agent      PAUSED_APPROVAL   2026-02-23 10:22:00
```

| Flag | Description |
|------|-------------|
| `--agent` | Filter by agent name |

### `runs get`

```bash
runagents runs get <run-id>
```

Displays run details including status, agent, timestamps, and error information.

### `runs events`

```bash
runagents runs events <run-id>
```

```
SEQ  TYPE               DETAIL                              TIME
1    TOOL_CALL          Called echo-tool                     10:15:01
2    LLM_CALL           gpt-4o-mini                         10:15:02
3    TOOL_CALL          Called stripe-api (POST /v1/charges) 10:15:03
4    APPROVAL_REQUIRED  stripe-api: charges.create           10:15:03
5    APPROVAL_GRANTED   Approved by admin@company.com        10:18:30
6    TOOL_CALL          Retried stripe-api                   10:18:31
7    COMPLETED          Run finished successfully            10:18:35
```

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
```

Approves the access request, creating a time-limited policy binding (default 4h).

### `approvals reject`

```bash
runagents approvals reject <request-id>
```

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
