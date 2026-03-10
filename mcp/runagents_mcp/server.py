"""RunAgents MCP Server — 14 tools for the RunAgents platform API."""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    """Load config from env vars, falling back to ~/.runagents/config.json."""
    cfg = {"endpoint": "http://localhost:8092", "api_key": "", "namespace": "default"}

    # Try config file first
    config_path = Path.home() / ".runagents" / "config.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            if data.get("endpoint"):
                cfg["endpoint"] = data["endpoint"]
            if data.get("api_key"):
                cfg["api_key"] = data["api_key"]
            if data.get("namespace"):
                cfg["namespace"] = data["namespace"]
        except (json.JSONDecodeError, OSError):
            pass

    # Env vars override
    if os.environ.get("RUNAGENTS_ENDPOINT"):
        cfg["endpoint"] = os.environ["RUNAGENTS_ENDPOINT"]
    if os.environ.get("RUNAGENTS_API_KEY"):
        cfg["api_key"] = os.environ["RUNAGENTS_API_KEY"]
    if os.environ.get("RUNAGENTS_NAMESPACE"):
        cfg["namespace"] = os.environ["RUNAGENTS_NAMESPACE"]

    # Strip trailing slash
    cfg["endpoint"] = cfg["endpoint"].rstrip("/")
    return cfg


_config = _load_config()


def _headers() -> dict:
    """Build HTTP headers matching cli/internal/client/client.go."""
    h = {"Content-Type": "application/json"}
    if _config["namespace"]:
        h["X-Workspace-Namespace"] = _config["namespace"]
    if _config["api_key"]:
        h["Authorization"] = f"Bearer {_config['api_key']}"
        if _config["api_key"].startswith("ra_ws_"):
            h["X-RunAgents-API-Key"] = _config["api_key"]
    return h


def _request(method: str, path: str, body: dict | None = None) -> dict | list | str:
    """Make an HTTP request to the RunAgents API."""
    url = _config["endpoint"] + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return {"error": f"HTTP {e.code}", "detail": error_body}
    except urllib.error.URLError as e:
        return {"error": f"Connection failed: {e.reason}"}


def _get(path: str) -> dict | list | str:
    return _request("GET", path)


def _post(path: str, body: dict | None = None) -> dict | list | str:
    return _request("POST", path, body)


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
    result = _get("/api/agents")
    return json.dumps(result, indent=2)


@mcp.tool()
def get_agent(namespace: str, name: str) -> str:
    """Get detailed information about a specific agent.

    Args:
        namespace: Agent namespace (e.g., "default", "agent-system")
        name: Agent name
    """
    result = _get(f"/api/agents/{namespace}/{name}")
    return json.dumps(result, indent=2)


@mcp.tool()
def list_tools() -> str:
    """List all registered tools with their base URLs, auth types, and access control settings."""
    result = _get("/api/tools")
    return json.dumps(result, indent=2)


@mcp.tool()
def list_models() -> str:
    """List all model providers with their supported models and status."""
    result = _get("/api/model-providers")
    return json.dumps(result, indent=2)


@mcp.tool()
def list_runs(agent: str = "", limit: int = 20) -> str:
    """List agent runs, optionally filtered by agent name.

    Args:
        agent: Filter by agent name (optional)
        limit: Maximum number of runs to return (default 20)
    """
    path = "/runs"
    params = []
    if agent:
        params.append(f"agent={agent}")
    if limit != 20:
        params.append(f"limit={limit}")
    if params:
        path += "?" + "&".join(params)
    result = _get(path)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_run_events(run_id: str) -> str:
    """Get the event timeline for a specific run, including tool calls and approvals.

    Args:
        run_id: The run ID
    """
    result = _get(f"/runs/{run_id}/events")
    return json.dumps(result, indent=2)


@mcp.tool()
def export_context() -> str:
    """Export the full workspace context — agents, tools, models, policies, approvals, and drafts."""
    result = _get("/api/context/export")
    return json.dumps(result, indent=2)


@mcp.tool()
def analyze_code(files: dict[str, str]) -> str:
    """Analyze source code to detect tool calls, LLM usage, secrets, and requirements.

    Args:
        files: Map of filename to source code content (e.g., {"agent.py": "import openai\\n..."})
    """
    result = _post("/ingestion/analyze", {"files": files})
    return json.dumps(result, indent=2)


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
    body: dict = {"agent_name": agent_name}
    if source_files:
        body["source_files"] = source_files
    if image:
        body["image"] = image
    if system_prompt:
        body["system_prompt"] = system_prompt
    if required_tools:
        body["required_tools"] = required_tools
    if tools_to_create:
        body["tools_to_create"] = tools_to_create
    if llm_configs:
        body["llm_configs"] = llm_configs
    if requirements:
        body["requirements"] = requirements
    if entry_point:
        body["entry_point"] = entry_point
    result = _post("/api/deploy", body)
    return json.dumps(result, indent=2)


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
    body = {
        "name": name,
        "base_url": base_url,
        "description": description,
        "auth_type": auth_type,
        "port": port,
        "scheme": scheme,
    }
    result = _post("/api/tools", body)
    return json.dumps(result, indent=2)


@mcp.tool()
def validate_plan(plan: dict) -> str:
    """Validate an action plan before applying it. Returns validation errors if any.

    Args:
        plan: The action plan object to validate
    """
    result = _post("/api/actions/validate", plan)
    return json.dumps(result, indent=2)


@mcp.tool()
def apply_plan(plan: dict) -> str:
    """Apply a validated action plan to the platform. Creates/updates resources.

    Args:
        plan: The action plan object to apply
    """
    result = _post("/api/actions/apply", plan)
    return json.dumps(result, indent=2)


@mcp.tool()
def approve_request(request_id: str) -> str:
    """Approve a pending access request, granting the agent time-limited access to the tool.

    Args:
        request_id: The access request ID
    """
    result = _post(f"/governance/requests/{request_id}/approve")
    return json.dumps(result, indent=2)


@mcp.tool()
def seed_starter_kit() -> str:
    """Create demo starter resources (echo-tool and playground-llm). Idempotent — safe to call multiple times."""
    result = _post("/api/starter-kit")
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the MCP server on stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
