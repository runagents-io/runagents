# RunAgents

**Deploy AI agents that act securely.** RunAgents is a platform for deploying and orchestrating AI agents with secure, policy-driven access to external tools and services.

Bring your own interface: a web app, WhatsApp, Slack, an internal portal, or a custom client. RunAgents owns execution, identity propagation, policy enforcement, approval workflows, and tool access behind the scenes.

- **Identity Propagation** — user identity flows from client → agent → tool
- **Policy-Driven Access** — fine-grained allow/deny rules, auto-binding, capability enforcement
- **Just-In-Time Approvals** — high-risk tool access pauses for admin sign-off with TTL expiry
- **LLM Gateway** — unified OpenAI-compatible endpoint for all model providers
- **Interface-Agnostic Runtime** — use the same governed agent behind any user-facing surface

## What's New

- **SDK & MCP v1.3.0** — catalog, governance, identity, and richer run operations now land on the public Python SDK and assistant tool surface
- **Scoped approvals** — approve one action, one run, or a short-lived user/agent/tool work window for governed writes
- **Agent catalog workflows** — start from richer blueprints such as the Google Workspace assistant for real policy, approval, and OAuth flows
- **Improved pause and resume behavior** — stronger operator and messaging-surface handling for approvals and consent

Read the latest release notes:

- [What's New](https://docs.runagents.io/whats-new/)
- [SDK & MCP v1.3.0 release notes](https://docs.runagents.io/whats-new/releases/2026-04-10-sdk-mcp-v1-3-0-parity/)
- [April 9, 2026 release notes](https://docs.runagents.io/whats-new/releases/2026-04-09-scoped-approvals-console-messaging/)

## Documentation

**[docs.runagents.io](https://docs.runagents.io)**

## Repository Surfaces

This public repository is currently the home for:

- `cli/` — the released Go CLI and install artifacts
- `sdk/python/` — the Python SDK and MCP server source
- `docs-site/` — the published documentation site
- `catalog/` — deployable catalog agents and manifests
- `skills/` — reusable assistant workflow packs
- `examples/` — sample agents and integration patterns

The goal is one coherent public source tree so the CLI, SDK, MCP, docs, catalog, and skills evolve together and ship on the same release line.

## Install

### Python SDK (recommended)

```bash
pip install runagents        # CLI + SDK + runtime
pip install runagents[mcp]   # + MCP server for AI coding assistants
```

```python
from runagents import Client, Agent

# Manage platform resources
client = Client()
agents = client.agents.list()

# Write agent code
agent = Agent()
result = agent.chat("What is 2+2?")
```

```bash
runagents init my-agent   # scaffold project
runagents dev             # local dev server
runagents deploy          # ship to platform
```

### CLI only

```bash
# macOS / Linux
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh

# npm
npm install -g @runagents/cli

# Homebrew
brew tap runagents-io/tap && brew install runagents
```

## Quick Start

```bash
# Configure
runagents config set endpoint https://api.runagents.io
runagents config set api-key YOUR_API_KEY

# Seed starter resources
runagents starter-kit

# Deploy an agent
runagents deploy --name my-agent --file agent.py --tool echo-tool --model openai/gpt-4o-mini

# Check runs
runagents runs list
```

## AI Assistant Setup (MCP)

Give Claude Code, Cursor, or Codex direct access to deploy and manage agents:

```bash
pip install runagents[mcp]
```

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "runagents": {
      "command": "runagents-mcp",
      "env": {
        "RUNAGENTS_ENDPOINT": "https://YOUR_WORKSPACE.try.runagents.io",
        "RUNAGENTS_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

See [AI Assistant Setup](https://docs.runagents.io/cli/ai-assistant-setup/) for full guide.
Use the public RunAgents skills library for reusable workflows across Codex, Claude Code, Cursor, and similar assistants around catalog deployment, tool onboarding, approvals, run debugging, and interface integrations such as WhatsApp: [RunAgents Skills](https://docs.runagents.io/cli/skills/).

## Get Access

Email **[try@runagents.io](mailto:try@runagents.io)** to request a free trial or sign up at [try.runagents.io](https://try.runagents.io).

## License

Apache 2.0
