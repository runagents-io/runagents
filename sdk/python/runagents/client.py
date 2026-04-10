"""Typed API client for the RunAgents platform (stdlib only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from runagents.config import Config, load_config
from runagents.types import (
    Agent, Tool, ModelProvider, Run, Event, DeployResult, AnalysisResult,
)


class Client:
    """RunAgents API client.

    Args:
        endpoint: Platform API URL (default: from config).
        api_key: API key or workspace token (default: from config).
        namespace: Target namespace (default: from config).
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        namespace: str | None = None,
    ):
        cfg = load_config()
        self.endpoint = (endpoint or cfg.endpoint).rstrip("/")
        self.api_key = api_key if api_key is not None else cfg.api_key
        self.namespace = namespace if namespace is not None else cfg.namespace

        self.agents = _AgentResource(self)
        self.tools = _ToolResource(self)
        self.models = _ModelResource(self)
        self.runs = _RunResource(self)
        self.approvals = _ApprovalResource(self)

    def __repr__(self) -> str:
        return f"Client(endpoint={self.endpoint!r}, namespace={self.namespace!r})"

    # --- Headers (matches cli/internal/client/client.go:158-168) ---

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self.namespace:
            h["X-Workspace-Namespace"] = self.namespace
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
            if self.api_key.startswith("ra_ws_"):
                h["X-RunAgents-API-Key"] = self.api_key
        return h

    # --- Low-level HTTP ---

    def _request(
        self, method: str, path: str, body: dict | None = None
    ) -> Any:
        url = self.endpoint + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            try:
                detail = json.loads(error_body)
            except (json.JSONDecodeError, ValueError):
                detail = error_body
            raise APIError(e.code, detail) from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"Connection failed: {e.reason}") from e

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, body: dict | None = None) -> Any:
        return self._request("POST", path, body)

    def patch(self, path: str, body: dict | None = None) -> Any:
        return self._request("PATCH", path, body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    # --- Standalone operations ---

    def analyze(self, files: dict[str, str]) -> AnalysisResult:
        """Analyze source code for tools, models, secrets."""
        result = self.post("/ingestion/analyze", {"files": files})
        return AnalysisResult.from_dict(result)

    def export_context(self) -> dict:
        """Export full workspace context."""
        return self.get("/api/context/export")

    def seed_starter_kit(self) -> dict:
        """Create demo starter resources (echo-tool + playground-llm)."""
        return self.post("/api/starter-kit")


class APIError(Exception):
    """Raised on HTTP error responses."""

    def __init__(self, status: int, detail: Any):
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status}: {detail}")


# ---------------------------------------------------------------------------
# Resource helpers
# ---------------------------------------------------------------------------


class _AgentResource:
    def __init__(self, client: Client):
        self._c = client

    def list(self) -> list[Agent]:
        result = self._c.get("/api/agents")
        if isinstance(result, list):
            return [Agent.from_dict(a) for a in result]
        return []

    def get(self, namespace: str, name: str) -> Agent:
        result = self._c.get(f"/api/agents/{namespace}/{name}")
        return Agent.from_dict(result)

    def deploy(
        self,
        name: str,
        source_files: dict[str, str] | None = None,
        image: str | None = None,
        system_prompt: str = "",
        required_tools: list[str] | None = None,
        tools_to_create: list[dict] | None = None,
        llm_configs: list[dict] | None = None,
        requirements: str = "",
        entry_point: str = "",
    ) -> DeployResult:
        body: dict[str, Any] = {"agent_name": name}
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
        result = self._c.post("/api/deploy", body)
        return DeployResult.from_dict(result)


class _ToolResource:
    def __init__(self, client: Client):
        self._c = client

    def list(self) -> list[Tool]:
        result = self._c.get("/api/tools")
        if isinstance(result, list):
            return [Tool.from_dict(t) for t in result]
        return []

    def get(self, name: str) -> Tool:
        result = self._c.get(f"/api/tools/{name}")
        return Tool.from_dict(result)

    def create(
        self,
        name: str,
        base_url: str,
        description: str = "",
        auth_type: str = "None",
        port: int = 443,
        scheme: str = "HTTPS",
    ) -> dict:
        body = {
            "name": name,
            "base_url": base_url,
            "description": description,
            "auth_type": auth_type,
            "port": port,
            "scheme": scheme,
        }
        return self._c.post("/api/tools", body)


class _ModelResource:
    def __init__(self, client: Client):
        self._c = client

    def list(self) -> list[ModelProvider]:
        result = self._c.get("/api/model-providers")
        if isinstance(result, list):
            return [ModelProvider.from_dict(m) for m in result]
        return []


class _RunResource:
    def __init__(self, client: Client):
        self._c = client

    def list(self, agent: str = "", limit: int = 20) -> list[Run]:
        path = "/runs"
        params = []
        if agent:
            params.append(f"agent={agent}")
        if limit != 20:
            params.append(f"limit={limit}")
        if params:
            path += "?" + "&".join(params)
        result = self._c.get(path)
        if isinstance(result, list):
            return [Run.from_dict(r) for r in result]
        return []

    def events(self, run_id: str) -> list[Event]:
        result = self._c.get(f"/runs/{run_id}/events")
        if isinstance(result, list):
            return [Event.from_dict(e) for e in result]
        return []


class _ApprovalResource:
    def __init__(self, client: Client):
        self._c = client

    def list(self) -> list[dict]:
        result = self._c.get("/governance/requests")
        return result if isinstance(result, list) else []

    def approve(self, request_id: str) -> dict:
        return self._c.post(f"/governance/requests/{request_id}/approve")

    def reject(self, request_id: str) -> dict:
        return self._c.post(f"/governance/requests/{request_id}/reject")
