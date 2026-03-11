"""RunAgents MCP Server — re-exports from runagents.mcp.server.

All tool implementations now live in the unified runagents package.
This file maintains backward compatibility for ``runagents-mcp`` installs.
"""

from runagents.mcp.server import mcp, main  # noqa: F401

__all__ = ["mcp", "main"]

if __name__ == "__main__":
    main()
