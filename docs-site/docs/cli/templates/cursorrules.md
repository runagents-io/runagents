# .cursorrules — RunAgents Agent Project

This project deploys to RunAgents, a platform for orchestrating AI agents with secure, policy-driven access to external tools and services.

## Platform

- Docs: https://docs.runagents.io
- CLI: `runagents` (install: `npm install -g @runagents/cli` or `brew install runagents-io/tap/runagents`)

## Key Commands

```bash
runagents deploy --files agent.py --name my-agent    # Deploy agent
runagents analyze --files agent.py                    # Preview code analysis
runagents agents list                                 # List agents
runagents tools list                                  # List registered tools
runagents models list                                 # List model providers
runagents runs list --agent my-agent                  # Monitor runs
runagents approvals list                              # Check pending approvals
runagents approvals approve <id>                      # Approve access request
```

## Agent Code Patterns

Agents are Python files deployed to RunAgents. The platform injects tool URLs, LLM gateway URL, and credentials as environment variables. Agent code never handles API keys.

### Tier 1 — Platform runtime (no custom code needed)
```python
import os, json, urllib.request
TOOL_URL = os.environ["TOOL_URL_MY_TOOL"]
LLM_URL = os.environ["LLM_GATEWAY_URL"]
```

### Tier 2 — Custom handler
```python
def handler(request, context):
    # context.tools, context.llm_url, context.model, context.system_prompt
    return {"response": "..."}
```

### Tier 2 — OpenAI SDK / LangChain / LangGraph
```python
import openai  # OPENAI_BASE_URL auto-set to LLM Gateway by platform
client = openai.OpenAI()
```

## Environment Variables (injected at runtime)

- `TOOL_URL_{NAME}` — Base URL for each required tool
- `LLM_GATEWAY_URL` — LLM Gateway endpoint
- `LLM_MODEL` — Model name (e.g., gpt-4o-mini)
- `SYSTEM_PROMPT` — Agent's system prompt
- `TOOL_DEFINITIONS_JSON` — OpenAI-format tool definitions
- `OPENAI_BASE_URL` — Auto-set to LLM Gateway for SDK compatibility

## Workflow

1. Write agent code using HTTP calls to tool URLs and the LLM gateway
2. Run `runagents analyze --files agent.py` to verify detection
3. Register tools via `runagents tools create` or the console
4. Deploy with `runagents deploy --files agent.py --name my-agent`
5. Monitor with `runagents runs list` and handle approvals with `runagents approvals`

## Important

- All outbound HTTP calls from agents are intercepted for policy checks and token injection
- Tools must be registered on the platform before agents can call them
- Use literal URL strings in `requests.post(...)` calls for the analysis engine to detect tools
- The platform handles OAuth2, API key injection, and identity propagation transparently
