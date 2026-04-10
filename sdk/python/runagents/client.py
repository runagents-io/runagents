"""Typed API client for the RunAgents platform (stdlib only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from runagents.config import Config, load_config
from runagents.types import (
    Agent, Tool, ModelProvider, Run, Event, DeployResult, AnalysisResult,
    CatalogListResponse, CatalogManifest, CatalogVersionsResponse,
    Policy, PolicyRule, ApprovalConnector, ApprovalConnectorDefaults,
    ApprovalConnectorActivity, ApprovalConnectorTestResult,
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
        self.catalog = _CatalogResource(self)
        self.policies = _PolicyResource(self)
        self.approval_connectors = _ApprovalConnectorResource(self)

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

    def get_with_query(self, path: str, query: dict[str, Any] | None = None) -> Any:
        if query:
            encoded = urllib.parse.urlencode(query, doseq=True)
            if encoded:
                separator = "&" if "?" in path else "?"
                path = f"{path}{separator}{encoded}"
        return self.get(path)

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


class _CatalogResource:
    def __init__(self, client: Client):
        self._c = client

    def list(
        self,
        search: str = "",
        categories: list[str] | None = None,
        tags: list[str] | None = None,
        integrations: list[str] | None = None,
        governance: list[str] | None = None,
        page: int = 1,
        page_size: int = 24,
    ) -> CatalogListResponse:
        query = _catalog_list_query(search, categories, tags, integrations, governance, page, page_size)
        result = self._c.get_with_query("/api/catalog", query)
        return CatalogListResponse.from_dict(result if isinstance(result, dict) else {})

    def get(self, agent_id: str, version: str = "") -> CatalogManifest:
        path = f"/api/catalog/{urllib.parse.quote(agent_id, safe='')}"
        if version.strip():
            path += "?" + urllib.parse.urlencode({"version": version.strip()})
        result = self._c.get(path)
        return CatalogManifest.from_dict(result if isinstance(result, dict) else {})

    def versions(self, agent_id: str) -> CatalogVersionsResponse:
        path = f"/api/catalog/{urllib.parse.quote(agent_id, safe='')}/versions"
        result = self._c.get(path)
        return CatalogVersionsResponse.from_dict(result if isinstance(result, dict) else {})

    def deploy(
        self,
        agent_id: str,
        version: str = "",
        name: str = "",
        tools: list[str] | None = None,
        model: str = "",
        policies: list[str] | None = None,
        identity_provider: str = "",
    ) -> DeployResult:
        manifest = self.get(agent_id, version=version)
        payload = _build_catalog_deploy_payload(
            manifest,
            name=name,
            tools=tools,
            model=model,
            policies=policies,
            identity_provider=identity_provider,
        )
        result = self._c.post("/api/deploy", payload)
        return DeployResult.from_dict(result if isinstance(result, dict) else {})


class _PolicyResource:
    def __init__(self, client: Client):
        self._c = client

    def list(self) -> list[Policy]:
        result = self._c.get("/api/policies")
        if isinstance(result, list):
            return [Policy.from_dict(item) for item in result]
        return []

    def get(self, name: str) -> Policy:
        result = self._c.get(f"/api/policies/{urllib.parse.quote(name, safe='')}")
        return Policy.from_dict(result if isinstance(result, dict) else {})

    def apply(self, document: dict[str, Any], name: str = "") -> Policy:
        request = _normalize_policy_apply_request(document, name)
        path = f"/api/policies/{urllib.parse.quote(request['name'], safe='')}"
        try:
            self._c.get(path)
        except APIError as exc:
            if exc.status != 404:
                raise
            result = self._c.post("/api/policies", request)
            return Policy.from_dict(result if isinstance(result, dict) else {})
        result = self._c._request("PUT", path, request)
        return Policy.from_dict(result if isinstance(result, dict) else {})

    def delete(self, name: str) -> dict[str, Any]:
        result = self._c.delete(f"/api/policies/{urllib.parse.quote(name, safe='')}")
        return result if isinstance(result, dict) else {"status": result}

    def translate(self, text: str) -> list[PolicyRule]:
        result = self._c.post("/api/policies/translate", {"text": text})
        if isinstance(result, dict):
            return [PolicyRule.from_dict(item) for item in result.get("rules", [])]
        return []


class _ApprovalConnectorResource:
    def __init__(self, client: Client):
        self._c = client

    def list(self) -> list[ApprovalConnector]:
        result = self._c.get("/api/settings/approval-connectors")
        if isinstance(result, list):
            return [ApprovalConnector.from_dict(item) for item in result]
        return []

    def get(self, connector_id: str) -> ApprovalConnector:
        result = self._c.get(f"/api/settings/approval-connectors/{urllib.parse.quote(connector_id, safe='')}")
        return ApprovalConnector.from_dict(result if isinstance(result, dict) else {})

    def apply(self, document: dict[str, Any]) -> ApprovalConnector:
        request = _normalize_approval_connector_apply_request(document)
        target = _resolve_approval_connector_target(self.list(), request)
        if target is None:
            create_request = _build_approval_connector_create(request)
            result = self._c.post("/api/settings/approval-connectors", create_request)
            return ApprovalConnector.from_dict(result if isinstance(result, dict) else {})
        patch = _build_approval_connector_patch(request)
        result = self._c.patch(f"/api/settings/approval-connectors/{urllib.parse.quote(target.id, safe='')}", patch)
        return ApprovalConnector.from_dict(result if isinstance(result, dict) else {})

    def delete(self, connector_id: str) -> dict[str, Any]:
        result = self._c.delete(f"/api/settings/approval-connectors/{urllib.parse.quote(connector_id, safe='')}")
        return result if isinstance(result, dict) else {"status": result}

    def test(self, connector_id: str) -> ApprovalConnectorTestResult:
        connector = self.get(connector_id)
        result = self._c.post("/api/settings/approval-connectors/test", _build_approval_connector_test_request(connector))
        return ApprovalConnectorTestResult.from_dict(result if isinstance(result, dict) else {})

    def defaults_get(self) -> ApprovalConnectorDefaults:
        result = self._c.get("/api/settings/approval-connectors/defaults")
        return ApprovalConnectorDefaults.from_dict(result if isinstance(result, dict) else {})

    def defaults_set(
        self,
        delivery_mode: str | None = None,
        fallback_to_ui: bool | None = None,
        timeout_seconds: int | None = None,
    ) -> ApprovalConnectorDefaults:
        body: dict[str, Any] = {}
        if delivery_mode is not None:
            body["default_delivery_mode"] = delivery_mode
        if fallback_to_ui is not None:
            body["default_fallback_to_ui"] = fallback_to_ui
        if timeout_seconds is not None:
            body["default_timeout_seconds"] = timeout_seconds
        result = self._c._request("PUT", "/api/settings/approval-connectors/defaults", body)
        return ApprovalConnectorDefaults.from_dict(result if isinstance(result, dict) else {})

    def activity(self, limit: int = 50) -> list[ApprovalConnectorActivity]:
        query = {"limit": limit} if limit > 0 else None
        result = self._c.get_with_query("/api/settings/approval-connectors/activity", query)
        if isinstance(result, list):
            return [ApprovalConnectorActivity.from_dict(item) for item in result]
        return []


def _catalog_list_query(
    search: str,
    categories: list[str] | None,
    tags: list[str] | None,
    integrations: list[str] | None,
    governance: list[str] | None,
    page: int,
    page_size: int,
) -> dict[str, list[str] | str]:
    query: dict[str, list[str] | str] = {}
    if search.strip():
        query["search"] = search.strip()
    if categories:
        query["category"] = [item.strip() for item in categories if item.strip()]
    if tags:
        query["tag"] = [item.strip() for item in tags if item.strip()]
    if integrations:
        query["integration"] = [item.strip() for item in integrations if item.strip()]
    if governance:
        query["governance"] = [item.strip() for item in governance if item.strip()]
    if page > 0:
        query["page"] = str(page)
    if page_size > 0:
        query["page_size"] = str(page_size)
    return query


def _resolve_catalog_llm_configs(default_model: str, override_model: str) -> list[dict[str, str]]:
    model_value = override_model.strip()
    if not model_value:
        model_value = default_model.strip()
        if model_value and "/" not in model_value:
            model_value = "openai/" + model_value
    if not model_value:
        return []
    parts = model_value.split("/", 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise ValueError(f"catalog deploy model must be in provider/model format; got {model_value!r}")
    return [{"provider": parts[0].strip(), "model": parts[1].strip(), "role": "default"}]


def _build_catalog_deploy_payload(
    manifest: CatalogManifest,
    name: str = "",
    tools: list[str] | None = None,
    model: str = "",
    policies: list[str] | None = None,
    identity_provider: str = "",
) -> dict[str, Any]:
    agent_name = name.strip() or manifest.deployment_template.agent_name.strip() or manifest.id.strip()
    if not agent_name:
        raise ValueError("catalog manifest is missing an agent name")

    required_tools = list(manifest.deployment_template.required_tools)
    if tools:
        required_tools = [item for item in tools if item.strip()]

    policy_names = list(manifest.deployment_template.policies)
    if policies:
        policy_names = [item for item in policies if item.strip()]

    resolved_identity_provider = identity_provider.strip() or manifest.deployment_template.identity_provider.strip()

    payload: dict[str, Any] = {
        "agent_name": agent_name,
        "source_files": dict(manifest.deployment_template.source_files),
    }
    if manifest.deployment_template.system_prompt.strip():
        payload["system_prompt"] = manifest.deployment_template.system_prompt.strip()
    if required_tools:
        payload["required_tools"] = required_tools
    if policy_names:
        payload["policies"] = policy_names
    if resolved_identity_provider:
        payload["identity_provider"] = resolved_identity_provider

    llm_configs = _resolve_catalog_llm_configs(manifest.default_model, model)
    if llm_configs:
        payload["llm_configs"] = llm_configs
    return payload


def _normalize_policy_apply_request(document: dict[str, Any], override_name: str = "") -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("policy document must be an object")
    if "spec" in document:
        name = override_name.strip() or str(document.get("name", "")).strip()
        spec = document.get("spec", {})
    else:
        name = override_name.strip() or str(document.get("name", "")).strip()
        spec = document
    if not name:
        raise ValueError("policy name is required")
    if not isinstance(spec, dict):
        raise ValueError("policy spec must be an object")
    return {"name": name, "spec": spec}


def _normalize_approval_connector_apply_request(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("approval connector document must be an object")
    normalized = dict(document)
    normalized["id"] = str(normalized.get("id", "")).strip()
    normalized["name"] = str(normalized.get("name", "")).strip()
    normalized["type"] = str(normalized.get("type", "")).strip()
    normalized["endpoint"] = str(normalized.get("endpoint", "")).strip()
    normalized["slack_security_mode"] = str(normalized.get("slack_security_mode", "")).strip()
    if not normalized["id"] and not normalized["name"]:
        raise ValueError("connector document must include either id or name")
    return normalized


def _resolve_approval_connector_target(
    connectors: list[ApprovalConnector],
    request: dict[str, Any],
) -> ApprovalConnector | None:
    connector_id = request.get("id", "")
    if connector_id:
        for connector in connectors:
            if connector.id == connector_id:
                return connector
    name = request.get("name", "")
    if not name:
        return None
    matches = [connector for connector in connectors if connector.name == name]
    if len(matches) > 1:
        raise ValueError(f"multiple approval connectors share the name {name!r}; use an id instead")
    return matches[0] if matches else None


def _build_approval_connector_create(request: dict[str, Any]) -> dict[str, Any]:
    if not request.get("name"):
        raise ValueError("connector name is required when creating a connector")
    if not request.get("endpoint"):
        raise ValueError("connector endpoint is required when creating a connector")
    body: dict[str, Any] = {
        "name": request["name"],
        "endpoint": request["endpoint"],
    }
    for key in ("type", "headers", "enabled", "timeout_seconds"):
        if key in request and request[key] not in ("", None):
            body[key] = request[key]
    if request.get("slack_security_mode"):
        body["slack_security_mode"] = request["slack_security_mode"]
    return body


def _build_approval_connector_patch(request: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {}
    for key in ("name", "type", "endpoint", "headers", "enabled", "timeout_seconds"):
        if key in request and request[key] not in ("", None):
            body[key] = request[key]
    if request.get("slack_security_mode"):
        body["slack_security_mode"] = request["slack_security_mode"]
    return body


def _build_approval_connector_test_request(connector: ApprovalConnector) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": connector.type,
        "endpoint": connector.endpoint,
    }
    if connector.headers:
        body["headers"] = connector.headers
    if connector.timeout_seconds:
        body["timeout_seconds"] = connector.timeout_seconds
    if connector.slack_security_mode:
        body["slack_security_mode"] = connector.slack_security_mode
    return body
