---
title: Python SDK
description: Install, configure, and use the RunAgents Python SDK — Client, Agent, CLI, MCP server, and runtime in one package.
---

# Python SDK

`pip install runagents` gives you everything in one zero-dependency package:

| What | How |
|------|-----|
| **Client** — manage platform resources from Python | `from runagents import Client` |
| **Agent** — write agent code with SDK helpers | `from runagents import Agent` |
| **`@tool` decorator** — mark tool handler functions | `from runagents import tool` |
| **CLI** — `init`, `dev`, `deploy` from the terminal | `runagents init my-agent` |
| **MCP server** — 14 tools for AI coding assistants | `pip install runagents[mcp]` |
| **Runtime** — HTTP server for deployed agents | auto-mounted by the platform |

---

## SDK, CLI, MCP, and Skills

RunAgents has four complementary developer surfaces:

- **CLI** — explicit operator commands from the terminal
- **Python SDK** — programmatic resource and runtime access from Python
- **MCP server** — structured tools for Claude Code, Cursor, Codex, and similar assistants
- **Skills** — reusable workflow guidance layered on top of CLI and MCP

The Python SDK and MCP server source now live in the public repo under `sdk/python/`. The CLI currently exposes the broadest public management surface. The MCP server focuses on the highest-value assistant workflows first and is being brought into parity with newer CLI areas such as catalog deployment, policies, approval connectors, identity providers, and richer run operations.

---

## Install

```bash
pip install runagents          # core — zero dependencies
pip install runagents[mcp]     # + MCP server (requires mcp>=1.0)
pip install runagents[dev]     # + hot-reload for local dev (requires watchdog)
```

Requires Python 3.10+.

---

## Configuration

The SDK reads config from `~/.runagents/config.json` (written by `runagents config set ...`) with environment variable overrides.

```bash
# Set via CLI (recommended)
runagents config set endpoint https://YOUR_WORKSPACE.try.runagents.io
runagents config set api-key  ra_ws_YOUR_KEY
runagents config set namespace default

# Or via environment variables
export RUNAGENTS_ENDPOINT=https://YOUR_WORKSPACE.try.runagents.io
export RUNAGENTS_API_KEY=ra_ws_YOUR_KEY
export RUNAGENTS_NAMESPACE=default
```

Config is stored at `~/.runagents/config.json` (permissions `0600`). Environment variables always take precedence.

| Variable | Default | Description |
|----------|---------|-------------|
| `RUNAGENTS_ENDPOINT` | `http://localhost:8092` | Platform API URL |
| `RUNAGENTS_API_KEY` | — | API key or workspace token (`ra_ws_...`) |
| `RUNAGENTS_NAMESPACE` | `default` | Target namespace |
| `RUNAGENTS_ASSISTANT_MODE` | `external` | `external`, `runagents`, or `off` |

---

## Client

The `Client` manages platform resources programmatically. Useful for CI/CD pipelines, deploy scripts, and monitoring tooling.

```python
from runagents import Client

client = Client()  # auto-loads from config + env vars
# or explicitly:
client = Client(
    endpoint="https://YOUR_WORKSPACE.try.runagents.io",
    api_key="ra_ws_...",
    namespace="default",
)
```

### Agents

```python
# List all agents
agents = client.agents.list()
for a in agents:
    print(a.name, a.namespace, a.status)

# Get a specific agent
agent = client.agents.get("default", "payment-agent")
print(agent.status)   # "Running" | "Pending" | "Failed"

# Deploy from source files
result = client.agents.deploy(
    name="payment-agent",
    source_files={"agent.py": open("agent.py").read()},
    system_prompt="You are a payment assistant.",
    required_tools=["stripe-api"],
    llm_configs=[{"provider": "openai", "model": "gpt-4o-mini", "role": "default"}],
    requirements="runagents>=1.2.1\n",
    entry_point="agent.py",
)
print(result.status)  # "created" | "updated"
```

### Tools

```python
# List registered tools
tools = client.tools.list()

# Register a new tool
client.tools.create(
    name="stripe-api",
    base_url="https://api.stripe.com",
    description="Stripe payment processing API",
    auth_type="APIKey",   # "None" | "APIKey" | "OAuth2"
    port=443,
    scheme="HTTPS",
)

# Get a specific tool
tool = client.tools.get("stripe-api")
```

### Runs

```python
# List recent runs for an agent
runs = client.runs.list(agent="payment-agent", limit=10)
for r in runs:
    print(r.id, r.status, r.created_at)

# Get the full event timeline for a run
events = client.runs.events(run_id)
for event in events:
    print(f"[{event.sequence}] {event.type}: {event.data}")
```

### Approvals

```python
# List pending access requests
approvals = client.approvals.list()

# Approve / reject
client.approvals.approve("req-abc123")
client.approvals.reject("req-abc123")
```

### Other operations

```python
# Analyze source code — returns AnalysisResult
result = client.analyze({"agent.py": open("agent.py").read()})
print(result.tools)              # detected tool calls
print(result.model_providers)    # detected LLM usage
print(result.entry_point)        # detected entry point
print(result.detected_requirements)

# Seed demo resources (echo-tool + playground-llm)
client.seed_starter_kit()

# Export full workspace context
ctx = client.export_context()
```

---

## Agent

The `Agent` class is for writing agent code. It reads operator-injected environment variables and exposes tool and LLM helpers.

```python
from runagents import Agent

agent = Agent()
```

The platform operator injects these env vars automatically at deploy time — you never set them manually in production:

| Env var | What it provides |
|---------|-----------------|
| `SYSTEM_PROMPT` | Agent's system prompt |
| `LLM_GATEWAY_URL` | LLM gateway chat completions URL |
| `LLM_MODEL` | Model name (e.g. `gpt-4o-mini`) |
| `TOOL_URL_{NAME}` | Base URL for each required tool |

### `agent.call_tool()`

Call a platform tool by name. The platform egress layer handles authentication and policy — the agent just makes an HTTP call.

```python
# POST request (default)
result = agent.call_tool(
    name="stripe-api",
    path="/v1/charges",
    payload={"amount": 1000, "currency": "usd"},
)

# GET request
product = agent.call_tool(
    name="product-catalog",
    path="/products/PRD-001",
    method="GET",
)
```

Tool names must match what's in `TOOL_URL_{NAME}` env vars (injected for every tool in `requiredTools`).

!!! info "Policy still applies"
    Tool calls are authorized by policies bound to the agent service account. If no matching `allow` or `approval_required` rule exists, calls are denied.

### `agent.chat()`

Call the LLM gateway with a message. Returns a standard OpenAI-format response.

```python
response = agent.chat(
    message="Summarise this order",
    tools=[...],        # optional — OpenAI tool definitions
    history=[...],      # optional — prior conversation messages
)
content = response["choices"][0]["message"]["content"]
```

Your OpenAI key never appears in agent code. The platform injects gateway credentials at runtime.

---

## @tool decorator

Mark functions as tool handlers for discovery and metadata:

```python
from runagents import tool

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

# With explicit name and description
@tool(name="weather-lookup", description="Get current weather for a city")
def get_weather(city: str) -> dict:
    ...

# Decorated functions get .tool_name and .tool_description attributes
print(calculate.tool_name)          # "calculate"
print(get_weather.tool_name)        # "weather-lookup"
print(get_weather.tool_description) # "Get current weather for a city"
```

---

## Writing agent handlers

The platform runtime discovers a `handler()` function in your entry point file. Three supported signatures:

```python
# 0 args — agent manages its own state
def handler():
    ...

# 1 arg — receives the request
def handler(request):
    message = request["message"]    # str
    history = request["history"]    # list[dict]
    ...

# 2 args — receives request + RunContext
def handler(request, ctx):
    message = request["message"]
    # ctx is a RunContext with agent metadata
    ...
```

Return a string or a dict with a `"response"` key:

```python
def handler(request, ctx):
    return "Hello!"
    # or:
    return {"response": "Hello!"}
```

See [Agent Runtime](../platform/agent-runtime.md) for the full RunContext API, SSE streaming, and resume-after-approval details.

---

## CLI

`pip install runagents` registers a `runagents` command that handles `init` and `dev` natively, and delegates everything else to the Go CLI binary (downloaded automatically on first use).

### `runagents init`

Scaffold a new agent project:

```bash
runagents init my-agent
cd my-agent
```

Creates:

```
my-agent/
├── agent.py          # handler function template
├── runagents.yaml    # tools, model, system prompt
├── requirements.txt  # pip dependencies
├── CLAUDE.md         # AI assistant context
├── .cursorrules      # Cursor context
├── AGENTS.md         # Universal AI context
├── .mcp.json         # MCP server config
└── .gitignore
```

### `runagents dev`

Start a local dev server:

```bash
runagents dev
```

Reads `runagents.yaml` and:

- Starts the agent runtime on `:8080`
- Starts a mock tool server on `:9090` (returns echo responses for every tool call)
- Routes `TOOL_URL_*` env vars to the mock server
- Connects to the platform LLM gateway if `RUNAGENTS_ENDPOINT` is set, or OpenAI directly if `OPENAI_API_KEY` is set

```bash
runagents dev --port 8081          # custom agent port
runagents dev --mock-port 9091     # custom mock tool port
runagents dev --no-mock            # no mock server (use real tool URLs)
runagents dev --watch              # hot-reload on .py changes (requires watchdog)
```

Test locally:

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### `runagents deploy`

Deploy to the platform (delegates to Go CLI):

```bash
runagents deploy \
  --name my-agent \
  --file agent.py \
  --tool echo-tool \
  --model openai/gpt-4o-mini
```

All other `runagents` commands (`agents`, `tools`, `runs`, `approvals`, etc.) also delegate to the Go CLI. See [CLI Commands](../cli/commands.md) for the full reference.

---

## MCP Server

Install with the `[mcp]` extra:

```bash
pip install runagents[mcp]
```

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "runagents": {
      "command": "runagents-mcp",
      "env": {
        "RUNAGENTS_ENDPOINT": "https://YOUR_WORKSPACE.try.runagents.io",
        "RUNAGENTS_API_KEY": "ra_ws_YOUR_KEY"
      }
    }
  }
}
```

This gives AI coding assistants (Claude Code, Cursor, Codex) 14 tools to deploy agents, manage tools, monitor runs, and handle approvals — without leaving the editor. See [AI Assistant Setup](../cli/ai-assistant-setup.md) for the full tool list and configuration guide.

---

## Runtime

The runtime (`runagents.runtime`) is the HTTP server that runs your agent in production. The platform mounts it automatically — you don't import it in agent code.

It provides:

- `POST /invoke` — sync request/response
- `POST /invoke/stream` — SSE streaming (tool call events, content deltas, done)
- `POST /resume/{action_id}` — resume after JIT approval
- `GET /readyz` — readiness probe (pings LLM gateway)
- `GET /healthz` — liveness probe

For backward compatibility, `import runagents_runtime` still works and resolves to `runagents.runtime`.

See [Agent Runtime](../platform/agent-runtime.md) for full documentation.

---

## PyPI

- Package: [`runagents`](https://pypi.org/project/runagents/)
- Current repo version: `1.2.1`
- Source: [github.com/runagents-io/runagents](https://github.com/runagents-io/runagents)
- License: Apache 2.0
