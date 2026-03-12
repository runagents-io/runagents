# CLAUDE.md — RunAgents Agent Project

This file configures Claude Code to work with the RunAgents platform for deploying and managing AI agents.

## Platform

This project deploys to **RunAgents** — a platform for orchestrating AI agents with secure, policy-driven access to external tools and services.

- **Docs**: https://docs.runagents.io
- **CLI**: `runagents` (install: `npm install -g @runagents/cli` or `brew install runagents-io/tap/runagents`)
- **MCP Server**: `pip install runagents-mcp` (enables direct platform access from Claude Code)

## Setup

```bash
# Configure CLI with your workspace
runagents config set endpoint https://YOUR_WORKSPACE.try.runagents.io
runagents config set api-key YOUR_API_KEY
runagents config set namespace default
```

## Key Commands

```bash
# Deploy this agent
runagents deploy --name my-agent --file agent.py

# Analyze source (preview detected tools + models)
runagents analyze --file agent.py

# List platform resources
runagents agents list
runagents tools list
runagents models list

# Monitor runs
runagents runs list --agent my-agent
runagents runs get <run-id>

# Manage approvals
runagents approvals list
runagents approvals approve <request-id>

# Action plan workflow (validate before apply)
runagents action validate --file plan.json
runagents action apply --file plan.json
```

## Agent Code Patterns

Agents are Python files that call tools via HTTP and use the LLM gateway. The platform injects all URLs and credentials as environment variables.

### Tier 1 — No custom code (platform runtime handles tool calling)
```python
import os, json, urllib.request
TOOL_URL = os.environ["TOOL_URL_MY_TOOL"]
LLM_URL = os.environ["LLM_GATEWAY_URL"]
```

### Tier 2 — Custom handler function
```python
def handler(request, context):
    # context.tools = {"tool-name": "http://..."}, context.llm_url, context.model
    return {"response": "..."}
```

### Tier 2 — Framework (LangChain, LangGraph, OpenAI SDK)
```python
import openai  # OPENAI_BASE_URL auto-set to LLM Gateway
client = openai.OpenAI()
```

## Environment Variables (injected at runtime)

| Variable | Description |
|----------|-------------|
| `TOOL_URL_{NAME}` | Base URL for each required tool |
| `LLM_GATEWAY_URL` | LLM Gateway endpoint |
| `LLM_MODEL` | Model name (e.g., gpt-4o-mini) |
| `SYSTEM_PROMPT` | Agent's system prompt |
| `TOOL_DEFINITIONS_JSON` | OpenAI-format tool definitions |
| `OPENAI_BASE_URL` | Auto-set to LLM Gateway for SDK compatibility |

## Workflow

1. Write agent code that calls tools via HTTP URLs and uses the LLM gateway
2. Run `runagents analyze --file agent.py` to verify detection
3. Register any new tools via `runagents tools create --file tool.json` or the console
4. Deploy with `runagents deploy --name my-agent --file agent.py`
5. Monitor with `runagents runs list --agent my-agent`
6. Handle approvals with `runagents approvals list` and `runagents approvals approve`

## Important

- Agent code never handles API keys — the platform injects credentials at the network layer
- All outbound HTTP calls from agents are intercepted for policy checks and token injection
- Tools must be registered on the platform before agents can call them
- Use `requests.post("https://actual-api.com/path", ...)` with literal URLs for the analysis engine to detect tool calls
