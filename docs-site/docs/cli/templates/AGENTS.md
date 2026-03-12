# AGENTS.md — RunAgents Agent Project

## Project

This project contains AI agent code that deploys to the **RunAgents** platform. RunAgents orchestrates agents with secure, policy-driven access to external tools and services.

## Capabilities

| Capability | Description |
|------------|-------------|
| Deploy agents | Upload Python source code; the platform analyzes, builds, and deploys |
| Register tools | Define external APIs (Stripe, GitHub, Slack, etc.) with auth and access control |
| Configure LLM providers | Route model calls through a unified gateway (OpenAI, Anthropic, Bedrock) |
| Monitor runs | Track agent invocations, events, and tool calls |
| Approve access | Just-in-time approval workflow for sensitive tool access |

## Tools

### RunAgents CLI (`runagents`)

Install: `npm install -g @runagents/cli` or `brew install runagents-io/tap/runagents`

| Command | Description |
|---------|-------------|
| `runagents deploy --name NAME --file agent.py` | Deploy agent from source |
| `runagents analyze --file agent.py` | Preview code analysis results |
| `runagents agents list` | List deployed agents |
| `runagents tools list` | List registered tools |
| `runagents tools create --file tool.json` | Register a new tool |
| `runagents models list` | List model providers |
| `runagents runs list --agent NAME` | List runs for an agent |
| `runagents approvals list` | List pending access requests |
| `runagents approvals approve ID` | Approve an access request |
| `runagents starter-kit` | Seed demo tools and model provider |

### RunAgents MCP Server (`runagents-mcp`)

Install: `pip install runagents-mcp`

Provides 14 tools for direct platform access: `list_agents`, `get_agent`, `list_tools`, `list_models`, `list_runs`, `get_run_events`, `export_context`, `analyze_code`, `deploy_agent`, `create_tool`, `validate_plan`, `apply_plan`, `approve_request`, `seed_starter_kit`.

## Workflows

### Deploy a new agent
1. Write agent code (Python) that calls tools via HTTP and uses the LLM gateway
2. Run `runagents analyze --file agent.py` to verify tool and LLM detection
3. Register any new tools with `runagents tools create`
4. Deploy with `runagents deploy --name my-agent --file agent.py`

### Add a new tool
1. Register: `runagents tools create --file stripe-tool.json`
2. Update agent code to call the new tool URL
3. Re-deploy the agent

### Handle approvals
1. Check: `runagents approvals list`
2. Review the request details
3. Approve: `runagents approvals approve <request-id>`

## References

- Documentation: https://docs.runagents.io
- Writing Agents: https://docs.runagents.io/getting-started/writing-agents/
- API Reference: https://docs.runagents.io/api/overview/
- Architecture: https://docs.runagents.io/concepts/architecture/
