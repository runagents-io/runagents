# RunAgents MCP Server

[Model Context Protocol](https://modelcontextprotocol.io/) server for the [RunAgents](https://runagents.io) AI agent platform. Gives AI coding assistants (Claude Code, Cursor, Codex) direct access to deploy agents, manage tools, monitor runs, and handle approvals.

## Install

```bash
pip install runagents-mcp
```

## Configure

### Claude Code

Add to your `settings.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "runagents": {
      "command": "runagents-mcp",
      "env": {
        "RUNAGENTS_ENDPOINT": "https://YOUR_WORKSPACE.try.runagents.io",
        "RUNAGENTS_API_KEY": "YOUR_API_KEY",
        "RUNAGENTS_NAMESPACE": "default"
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "runagents": {
      "command": "runagents-mcp",
      "env": {
        "RUNAGENTS_ENDPOINT": "https://YOUR_WORKSPACE.try.runagents.io",
        "RUNAGENTS_API_KEY": "YOUR_API_KEY",
        "RUNAGENTS_NAMESPACE": "default"
      }
    }
  }
}
```

## Configuration

The server reads configuration from environment variables, falling back to `~/.runagents/config.json` (shared with the RunAgents CLI):

| Variable | Description | Default |
|----------|-------------|---------|
| `RUNAGENTS_ENDPOINT` | Platform API URL | `http://localhost:8092` |
| `RUNAGENTS_API_KEY` | API key or workspace key | — |
| `RUNAGENTS_NAMESPACE` | Target namespace | `default` |

## Tools

| Tool | Description | Type |
|------|-------------|------|
| `list_agents` | List all deployed agents | Read |
| `get_agent` | Get details for a specific agent | Read |
| `list_tools` | List registered tools | Read |
| `list_models` | List model providers | Read |
| `list_runs` | List agent runs | Read |
| `get_run_events` | Get events for a specific run | Read |
| `export_context` | Export full workspace context | Read |
| `analyze_code` | Analyze source code for tool and LLM usage | Read |
| `deploy_agent` | Deploy an agent from source code or image | Mutate |
| `create_tool` | Register a new tool | Mutate |
| `validate_plan` | Validate an action plan before applying | Read |
| `apply_plan` | Apply a validated action plan | Mutate |
| `approve_request` | Approve a pending access request | Mutate |
| `seed_starter_kit` | Create demo tools and model provider | Mutate |

## Documentation

- [AI Assistant Setup](https://docs.runagents.io/cli/ai-assistant-setup/) — Full setup guide
- [RunAgents Docs](https://docs.runagents.io) — Platform documentation
- [CLI Reference](https://docs.runagents.io/cli/commands/) — CLI commands
