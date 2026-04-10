# RunAgents Python SDK

Everything you need to build, test, and deploy AI agents on [RunAgents](https://runagents.io) — in one package.

The public source for this package lives in `sdk/python/` in the
[`runagents-io/runagents`](https://github.com/runagents-io/runagents) repository so the CLI, SDK, MCP server,
docs, and skills ship together.

## Install

```bash
pip install runagents        # Core SDK + CLI + runtime (zero deps)
pip install runagents[mcp]   # + MCP server for AI coding assistants
pip install runagents[dev]   # + hot-reload for local dev
```

## Quickstart

```bash
runagents init my-agent      # Scaffold a project
cd my-agent
runagents dev                # Local dev server with mock tools
runagents deploy             # Ship to the platform
```

## Python API

### Client — manage platform resources

```python
from runagents import Client

client = Client()  # reads ~/.runagents/config.json + env vars

agents = client.agents.list()
tools = client.tools.list()
runs = client.runs.list(agent="payment-agent")

result = client.agents.deploy(
    name="my-agent",
    source_files={"agent.py": open("agent.py").read()},
    required_tools=["stripe-api"],
    llm_configs=[{"provider": "openai", "model": "gpt-4o-mini", "role": "default"}],
)
```

### Agent — write agent code

```python
from runagents import Agent, tool

agent = Agent()  # reads TOOL_URL_*, LLM_GATEWAY_URL, LLM_MODEL from env

# Call a platform tool (platform egress layer handles auth)
result = agent.call_tool("echo-tool", "/echo", {"message": "hello"})

# Chat via LLM gateway
response = agent.chat("What is 2+2?", tools=[...])

# Custom handler (Tier 2)
def handler(request, ctx):
    message = request["message"]
    result = agent.chat(message)
    return result["choices"][0]["message"]["content"]
```

### @tool decorator

```python
from runagents import tool

@tool(name="calculator", description="Evaluate math expressions")
def calculate(expression: str) -> str:
    return str(eval(expression))
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `runagents init [name]` | Scaffold a new agent project |
| `runagents dev` | Start local dev server with mock tools |
| `runagents deploy` | Deploy an agent (delegates to Go CLI) |
| `runagents catalog` | Browse and deploy catalog agents |
| `runagents policies` | Manage governance policies |
| `runagents approval-connectors` | Manage approval routing connectors |
| `runagents identity-providers` | Manage workspace identity providers |
| `runagents agents list` | List agents |
| `runagents tools list` | List tools |
| `runagents runs list` | List runs |
| `runagents context export` | Export assistant/workspace context |
| `runagents config` | Manage configuration |

## Runtime

The runtime provides the HTTP server for deployed agents — tool calling loop, SSE streaming, health checks, OAuth consent, and JIT approvals. It runs automatically inside the platform; for local development use `runagents dev`.

Policy enforcement remains active at runtime. Agents need bound policy rules (`allow` or `approval_required`) for tool calls.

```python
# Backward compatible — still works
import runagents_runtime
```

## MCP Server

```bash
pip install runagents[mcp]
runagents-mcp  # starts on stdio
```

14 tools for AI coding assistants (Claude Code, Cursor, Codex). See [AI Assistant Setup](https://docs.runagents.io/cli/ai-assistant-setup/).

## Configuration

Reads from `~/.runagents/config.json` with env var overrides:

| Variable | Description | Default |
|----------|-------------|---------|
| `RUNAGENTS_ENDPOINT` | Platform API URL | `http://localhost:8092` |
| `RUNAGENTS_API_KEY` | API key or workspace key | — |
| `RUNAGENTS_NAMESPACE` | Target namespace | `default` |

## Documentation

- [RunAgents Docs](https://docs.runagents.io)
- [Writing Agents](https://docs.runagents.io/getting-started/writing-agents/)
- [Agent Runtime](https://docs.runagents.io/platform/agent-runtime/)
- [AI Assistant Setup](https://docs.runagents.io/cli/ai-assistant-setup/)
- [CLI Commands](https://docs.runagents.io/cli/commands/)

## License

Apache-2.0
