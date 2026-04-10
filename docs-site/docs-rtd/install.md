# Installation

## Python SDK

```bash
pip install runagents
```

## Python SDK with MCP server

```bash
pip install runagents[mcp]
```

This installs:

- the `runagents` Python package
- the `runagents` project CLI entrypoint
- the `runagents-mcp` command for editor and assistant integrations

## Basic configuration

The SDK and MCP server both read:

- `RUNAGENTS_ENDPOINT`
- `RUNAGENTS_API_KEY`
- `RUNAGENTS_NAMESPACE`

or the shared CLI config file:

- `~/.runagents/config.json`
