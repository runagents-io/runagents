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

The RunAgents MCP server gives your AI assistant direct access to the platform API — listing agents, deploying code, managing tools, inspecting the catalog, managing policies, configuring approval connectors, and handling approvals — all without leaving your editor.

### Install

```bash
pip install runagents[mcp]   # includes the SDK plus the runagents-mcp command
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

The MCP server now exposes a broader assistant toolset that covers:

| Family | Tools |
|--------|-------|
| Workspace | `list_agents`, `get_agent`, `list_tools`, `list_models`, `list_runs`, `get_run`, `get_run_events`, `get_run_timeline`, `wait_for_run`, `export_run`, `export_context`, `analyze_code` |
| Deploy | `deploy_agent`, `create_tool`, `validate_plan`, `apply_plan`, `seed_starter_kit` |
| Catalog | `list_catalog_agents`, `get_catalog_agent`, `list_catalog_versions`, `deploy_catalog_agent` |
| Policies | `list_policies`, `get_policy`, `apply_policy`, `delete_policy`, `translate_policy` |
| Identity providers | `list_identity_providers`, `get_identity_provider`, `apply_identity_provider`, `delete_identity_provider` |
| Approval connectors | `list_approval_connectors`, `get_approval_connector`, `apply_approval_connector`, `delete_approval_connector`, `test_approval_connector`, `get_approval_connector_defaults`, `set_approval_connector_defaults`, `list_approval_connector_activity` |
| Approvals | `approve_request` with optional `scope` and `duration` |

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
- **Deploy from catalog**: "Show me the Google Workspace assistant manifest and deploy it with my workspace policies"
- **Register tools**: "Register the Stripe API as a tool with API key auth"
- **Design governance**: "Translate this approval policy into structured rules and apply it"
- **Configure identity**: "Create the Google OIDC identity provider for my workspace host"
- **Route approvals**: "Show approval connectors and test the Slack connector"
- **Monitor runs**: "Show me the latest runs for payment-agent and wait for the newest one to finish"
- **Handle approvals**: "List pending approvals and approve the one for stripe-api for this run only"
- **Analyze code**: "Analyze agent.py and tell me what tools it calls"
- **Export context**: "Show me all agents, tools, and model providers in my workspace"

---

## Next Steps

- [External Assistants](external-assistants.md) — Full guide to using RunAgents with external AI assistants
- [CLI Commands](commands.md) — All CLI commands reference
- [Deploy API](../api/deploy.md) — Programmatic deployment API
