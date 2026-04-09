---
title: AI Assistant Setup
description: Configure Claude Code, Cursor, Codex, and other AI coding assistants to work with RunAgents via templates and the MCP server.
---

# AI Assistant Setup

Set up your AI coding assistant to deploy and manage RunAgents agents directly from your editor. This guide covers template files for project context and the MCP server for live platform access.

---

## Template Files

Template files give your AI assistant context about RunAgents commands, agent code patterns, and deployment workflows. Copy the right file into your agent project's root directory.

### Claude Code — `CLAUDE.md`

```bash
curl -o CLAUDE.md https://docs.runagents.io/cli/templates/CLAUDE.md
```

Place `CLAUDE.md` in your project root. Claude Code reads it automatically and learns the RunAgents CLI commands, agent code patterns, and deployment workflow.

### Cursor — `.cursorrules`

```bash
curl -o .cursorrules https://docs.runagents.io/cli/templates/cursorrules.md
```

Place `.cursorrules` in your project root. Cursor reads it automatically.

### Universal — `AGENTS.md`

```bash
curl -o AGENTS.md https://docs.runagents.io/cli/templates/AGENTS.md
```

`AGENTS.md` is an emerging standard for describing project capabilities and tools. Works with any assistant that reads project-level markdown files.

---

## MCP Server

The RunAgents MCP server gives your AI assistant direct access to the platform API — listing agents, deploying code, managing tools, and handling approvals — all without leaving your editor.

### Install

```bash
pip install runagents[mcp]   # recommended — includes full SDK + CLI
# or
pip install runagents-mcp    # standalone MCP server only
```

### Configure for Claude Code

Add to your Claude Code `settings.json` (or project `.mcp.json`):

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

### Configure for Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json`):

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

### Available Tools

The MCP server exposes 14 tools:

| Tool | Description | Type |
|------|-------------|------|
| `list_agents` | List all deployed agents | Read |
| `get_agent` | Get agent details | Read |
| `list_tools` | List registered tools | Read |
| `list_models` | List model providers | Read |
| `list_runs` | List agent runs | Read |
| `get_run_events` | Get events for a run | Read |
| `export_context` | Export full workspace context | Read |
| `analyze_code` | Analyze source code for tools and LLM usage | Read |
| `deploy_agent` | Deploy an agent from source or image | Mutate |
| `create_tool` | Register a new tool | Mutate |
| `validate_plan` | Validate an action plan | Read |
| `apply_plan` | Apply an action plan | Mutate |
| `approve_request` | Approve a pending access request | Mutate |
| `seed_starter_kit` | Create demo tools and model provider | Mutate |

### Configuration

The MCP server reads configuration from environment variables or `~/.runagents/config.json` (the same config file used by the CLI):

| Source | Variable | Description |
|--------|----------|-------------|
| Env | `RUNAGENTS_ENDPOINT` | Platform API URL |
| Env | `RUNAGENTS_API_KEY` | API key or workspace key (`ra_ws_...`) |
| Env | `RUNAGENTS_NAMESPACE` | Target namespace (default: `default`) |
| File | `~/.runagents/config.json` | Fallback — shared with CLI |

Environment variables take precedence over the config file.

---

## RunAgents Skills

If you want more than templates and raw MCP access, use the public RunAgents skills library. These first-party skills package common production workflows for Codex, Claude Code, Cursor, and similar assistants, including catalog deployment, tool onboarding, approvals, run debugging, and anywhere-interface integration such as WhatsApp.

For Claude Code specifically, the skills can be imported through `CLAUDE.md` or wrapped as project slash commands under `.claude/commands/`.

- [RunAgents Skills](skills.md)

## What You Can Do

With the template file and MCP server configured, your AI assistant can:

- **Deploy agents**: "Deploy agent.py as payment-agent with the stripe-api tool"
- **Register tools**: "Register the Stripe API as a tool with API key auth"
- **Monitor runs**: "Show me the latest runs for payment-agent"
- **Handle approvals**: "List pending approvals and approve the one for stripe-api"
- **Analyze code**: "Analyze agent.py and tell me what tools it calls"
- **Export context**: "Show me all agents, tools, and model providers in my workspace"

---

## Next Steps

- [External Assistants](external-assistants.md) — Full guide to using RunAgents with external AI assistants
- [CLI Commands](commands.md) — All CLI commands reference
- [Deploy API](../api/deploy.md) — Programmatic deployment API
