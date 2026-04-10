"""RunAgents MCP Server — 14 tools for the RunAgents platform API.

Refactored to use ``runagents.client.Client`` instead of duplicated HTTP code.
All 14 tools are preserved with identical signatures and behavior.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from runagents.client import Client, APIError

# ---------------------------------------------------------------------------
# Lazy client — instantiated on first tool call
# ---------------------------------------------------------------------------

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client()
    return _client


def _safe_call(fn) -> str:
    """Call fn, return JSON on success or error dict on failure."""
    try:
        result = fn()
        return json.dumps(result, indent=2, default=str)
    except APIError as e:
        return json.dumps({"error": f"HTTP {e.status}", "detail": e.detail}, indent=2)
    except ConnectionError as e:
        return json.dumps({"error": str(e)}, indent=2)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "RunAgents",
    instructions=(
        "RunAgents platform server. Use these tools to deploy AI agents, "
        "manage tools, monitor runs, and handle approvals. "
        "Read tools are safe to call anytime. Mutate tools change platform state."
    ),
)


# --- Read tools ---


@mcp.tool()
def list_agents() -> str:
    """List all deployed agents with their status, namespace, and required tools."""
    def _call():
        return [a.__dict__ for a in _get_client().agents.list()]
    return _safe_call(_call)


@mcp.tool()
def get_agent(namespace: str, name: str) -> str:
    """Get detailed information about a specific agent.

    Args:
        namespace: Agent namespace (e.g., "default", "agent-system")
        name: Agent name
    """
    def _call():
        return _get_client().agents.get(namespace, name).__dict__
    return _safe_call(_call)


@mcp.tool()
def list_tools() -> str:
    """List all registered tools with their base URLs, auth types, and access control settings."""
    def _call():
        return [t.__dict__ for t in _get_client().tools.list()]
    return _safe_call(_call)


@mcp.tool()
def list_models() -> str:
    """List all model providers with their supported models and status."""
    def _call():
        return [m.__dict__ for m in _get_client().models.list()]
    return _safe_call(_call)


@mcp.tool()
def list_runs(agent: str = "", limit: int = 20) -> str:
    """List agent runs, optionally filtered by agent name.

    Args:
        agent: Filter by agent name (optional)
        limit: Maximum number of runs to return (default 20)
    """
    def _call():
        return [r.__dict__ for r in _get_client().runs.list(agent=agent, limit=limit)]
    return _safe_call(_call)


@mcp.tool()
def get_run_events(run_id: str) -> str:
    """Get the event timeline for a specific run, including tool calls and approvals.

    Args:
        run_id: The run ID
    """
    def _call():
        return [e.__dict__ for e in _get_client().runs.events(run_id)]
    return _safe_call(_call)


@mcp.tool()
def export_context() -> str:
    """Export the full workspace context — agents, tools, models, policies, approvals, and drafts."""
    return _safe_call(lambda: _get_client().export_context())


@mcp.tool()
def analyze_code(files: dict[str, str]) -> str:
    """Analyze source code to detect tool calls, LLM usage, secrets, and requirements.

    Args:
        files: Map of filename to source code content (e.g., {"agent.py": "import openai\\n..."})
    """
    def _call():
        return _get_client().analyze(files).__dict__
    return _safe_call(_call)


# --- Mutate tools ---


@mcp.tool()
def deploy_agent(
    agent_name: str,
    source_files: dict[str, str] | None = None,
    image: str | None = None,
    system_prompt: str = "",
    required_tools: list[str] | None = None,
    tools_to_create: list[dict] | None = None,
    llm_configs: list[dict] | None = None,
    requirements: str = "",
    entry_point: str = "",
) -> str:
    """Deploy an agent from source code or a pre-built image.

    Args:
        agent_name: Unique name for the agent
        source_files: Map of filename to source code (e.g., {"agent.py": "..."})
        image: Pre-built container image URI (alternative to source_files)
        system_prompt: System prompt for the agent's LLM context
        required_tools: Names of existing tools the agent needs
        tools_to_create: New tools to register (list of {name, base_url, description, auth_type})
        llm_configs: LLM configurations (list of {provider, model, role})
        requirements: Python pip requirements (newline-separated)
        entry_point: Entry point filename
    """
    def _call():
        return _get_client().agents.deploy(
            name=agent_name,
            source_files=source_files,
            image=image,
            system_prompt=system_prompt,
            required_tools=required_tools,
            tools_to_create=tools_to_create,
            llm_configs=llm_configs,
            requirements=requirements,
            entry_point=entry_point,
        ).__dict__
    return _safe_call(_call)


@mcp.tool()
def create_tool(
    name: str,
    base_url: str,
    description: str = "",
    auth_type: str = "None",
    port: int = 443,
    scheme: str = "HTTPS",
) -> str:
    """Register a new tool (external API) on the platform.

    Args:
        name: Unique tool name (e.g., "stripe-api")
        base_url: Tool endpoint URL (e.g., "https://api.stripe.com")
        description: What the tool does
        auth_type: Authentication type — "None", "APIKey", or "OAuth2"
        port: Target port (default 443)
        scheme: Protocol — "HTTPS" or "HTTP"
    """
    def _call():
        return _get_client().tools.create(
            name=name, base_url=base_url, description=description,
            auth_type=auth_type, port=port, scheme=scheme,
        )
    return _safe_call(_call)


@mcp.tool()
def validate_plan(plan: dict) -> str:
    """Validate an action plan before applying it. Returns validation errors if any.

    Args:
        plan: The action plan object to validate
    """
    return _safe_call(lambda: _get_client().post("/api/actions/validate", plan))


@mcp.tool()
def apply_plan(plan: dict) -> str:
    """Apply a validated action plan to the platform. Creates/updates resources.

    Args:
        plan: The action plan object to apply
    """
    return _safe_call(lambda: _get_client().post("/api/actions/apply", plan))


@mcp.tool()
def approve_request(request_id: str) -> str:
    """Approve a pending access request, granting the agent time-limited access to the tool.

    Args:
        request_id: The access request ID
    """
    return _safe_call(lambda: _get_client().approvals.approve(request_id))


@mcp.tool()
def seed_starter_kit() -> str:
    """Create demo starter resources (echo-tool and playground-llm). Idempotent — safe to call multiple times."""
    return _safe_call(lambda: _get_client().seed_starter_kit())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the MCP server on stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
