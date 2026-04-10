"""Response dataclasses for the RunAgents API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Agent:
    name: str = ""
    namespace: str = ""
    status: str = ""
    image: str = ""
    required_tools: list[str] = field(default_factory=list)
    system_prompt: str = ""
    created_at: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Agent":
        raw_status = d.get("status", "")
        status = raw_status.get("phase", "") if isinstance(raw_status, dict) else raw_status
        return cls(
            name=d.get("name", d.get("metadata", {}).get("name", "")),
            namespace=d.get("namespace", d.get("metadata", {}).get("namespace", "")),
            status=status,
            image=d.get("spec", {}).get("image", d.get("image", "")),
            required_tools=d.get("spec", {}).get("requiredTools", d.get("required_tools", [])),
            system_prompt=d.get("spec", {}).get("systemPrompt", d.get("system_prompt", "")),
            created_at=d.get("metadata", {}).get("creationTimestamp", d.get("created_at", "")),
        )


@dataclass
class Tool:
    name: str = ""
    description: str = ""
    base_url: str = ""
    auth_type: str = ""
    topology: str = ""
    access_mode: str = ""
    capabilities: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Tool":
        spec = d.get("spec", d)
        conn = spec.get("connection", {})
        return cls(
            name=d.get("name", d.get("metadata", {}).get("name", "")),
            description=spec.get("description", ""),
            base_url=conn.get("baseUrl", spec.get("base_url", "")),
            auth_type=conn.get("authentication", {}).get("type", spec.get("auth_type", "")),
            topology=spec.get("topology", ""),
            access_mode=spec.get("accessMode", spec.get("access_mode", "")),
            capabilities=spec.get("capabilities", []),
        )


@dataclass
class ModelProvider:
    name: str = ""
    provider: str = ""
    models: list[str] = field(default_factory=list)
    status: str = ""
    endpoint: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ModelProvider":
        spec = d.get("spec", d)
        return cls(
            name=d.get("name", d.get("metadata", {}).get("name", "")),
            provider=spec.get("provider", ""),
            models=spec.get("models", []),
            status=d.get("status", {}).get("phase", d.get("status", "")),
            endpoint=spec.get("endpoint", ""),
        )


@dataclass
class Run:
    id: str = ""
    agent: str = ""
    namespace: str = ""
    status: str = ""
    created_at: str = ""
    updated_at: str = ""
    message: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Run":
        return cls(
            id=d.get("id", ""),
            agent=d.get("agent", ""),
            namespace=d.get("namespace", ""),
            status=d.get("status", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            message=d.get("message", ""),
        )


@dataclass
class Event:
    id: str = ""
    run_id: str = ""
    type: str = ""
    data: dict = field(default_factory=dict)
    sequence: int = 0
    created_at: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(
            id=d.get("id", ""),
            run_id=d.get("run_id", ""),
            type=d.get("type", ""),
            data=d.get("data", {}),
            sequence=d.get("sequence", 0),
            created_at=d.get("created_at", ""),
        )


@dataclass
class DeployResult:
    agent_name: str = ""
    namespace: str = ""
    tools_created: list[str] = field(default_factory=list)
    status: str = ""
    message: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "DeployResult":
        return cls(
            agent_name=d.get("agent_name", ""),
            namespace=d.get("namespace", ""),
            tools_created=d.get("tools_created", []),
            status=d.get("status", ""),
            message=d.get("message", ""),
        )


@dataclass
class AnalysisResult:
    id: str = ""
    framework: str = ""
    runtime_family: str = ""
    adapter: str = ""
    tools: list[dict] = field(default_factory=list)
    model_providers: list[dict] = field(default_factory=list)
    model_usages: list[dict] = field(default_factory=list)
    secrets: list[dict] = field(default_factory=list)
    outbound_destinations: list[dict] = field(default_factory=list)
    detected_requirements: list[str] = field(default_factory=list)
    entry_point: str = ""
    system_prompt_suggestion: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "AnalysisResult":
        return cls(
            id=d.get("id", ""),
            framework=d.get("framework", ""),
            runtime_family=d.get("runtime_family", ""),
            adapter=d.get("adapter", ""),
            tools=d.get("tools", []),
            model_providers=d.get("model_providers", []),
            model_usages=d.get("model_usages", []),
            secrets=d.get("secrets", []),
            outbound_destinations=d.get("outbound_destinations", []),
            detected_requirements=d.get("detected_requirements", []),
            entry_point=d.get("entry_point", ""),
            system_prompt_suggestion=d.get("system_prompt_suggestion", ""),
        )
