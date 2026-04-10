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
    conversation_id: str = ""
    agent_id: str = ""
    agent: str = ""
    agent_uid: str = ""
    namespace: str = ""
    user_id: str = ""
    surface_turn_id: str = ""
    status: str = ""
    blocked_action_id: str = ""
    initial_message: str = ""
    invoke_url: str = ""
    created_at: str = ""
    updated_at: str = ""
    message: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Run":
        agent_id = d.get("agent_id", d.get("agent", ""))
        return cls(
            id=d.get("id", ""),
            conversation_id=d.get("conversation_id", ""),
            agent_id=agent_id,
            agent=agent_id,
            agent_uid=d.get("agent_uid", ""),
            namespace=d.get("namespace", ""),
            user_id=d.get("user_id", ""),
            surface_turn_id=d.get("surface_turn_id", ""),
            status=d.get("status", ""),
            blocked_action_id=d.get("blocked_action_id", ""),
            initial_message=d.get("initial_message", ""),
            invoke_url=d.get("invoke_url", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            message=d.get("message", d.get("initial_message", "")),
        )


@dataclass
class Event:
    event_id: str = ""
    id: str = ""
    run_id: str = ""
    seq: int = 0
    type: str = ""
    payload_hash: str = ""
    actor: str = ""
    data: dict = field(default_factory=dict)
    sequence: int = 0
    timestamp: str = ""
    created_at: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        event_id = d.get("event_id", d.get("id", ""))
        seq = d.get("seq", d.get("sequence", 0))
        timestamp = d.get("timestamp", d.get("created_at", ""))
        return cls(
            event_id=event_id,
            id=event_id,
            run_id=d.get("run_id", ""),
            seq=seq,
            type=d.get("type", ""),
            payload_hash=d.get("payload_hash", ""),
            actor=d.get("actor", ""),
            data=d.get("data", {}),
            sequence=seq,
            timestamp=timestamp,
            created_at=timestamp,
        )


@dataclass
class RunTimelineEntry:
    seq: int = 0
    type: str = ""
    actor: str = ""
    summary: str = ""
    timestamp: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunExport:
    run: Run = field(default_factory=Run)
    events: list[Event] = field(default_factory=list)
    timeline: list[RunTimelineEntry] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    id: str = ""
    subject: str = ""
    agent_id: str = ""
    tool_id: str = ""
    status: str = ""
    duration: str = ""
    scope: str = ""
    approver_id: str = ""
    reason: str = ""
    action_id: str = ""
    run_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    expires_at: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalRequest":
        return cls(
            id=d.get("id", ""),
            subject=d.get("subject", ""),
            agent_id=d.get("agent_id", d.get("agent", "")),
            tool_id=d.get("tool_id", d.get("tool", "")),
            status=d.get("status", ""),
            duration=d.get("duration", ""),
            scope=d.get("scope", ""),
            approver_id=d.get("approver_id", ""),
            reason=d.get("reason", ""),
            action_id=d.get("action_id", ""),
            run_id=d.get("run_id", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            expires_at=d.get("expires_at", ""),
        )


@dataclass
class IdentityProviderConfig:
    issuer: str = ""
    jwks_uri: str = ""
    audiences: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "IdentityProviderConfig":
        return cls(
            issuer=d.get("issuer", ""),
            jwks_uri=d.get("jwksUri", d.get("jwks_uri", "")),
            audiences=d.get("audiences", []),
        )


@dataclass
class IdentityProviderSpec:
    host: str = ""
    identity_provider: IdentityProviderConfig = field(default_factory=IdentityProviderConfig)
    user_id_claim: str = ""
    allowed_domains: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "IdentityProviderSpec":
        return cls(
            host=d.get("host", ""),
            identity_provider=IdentityProviderConfig.from_dict(d.get("identityProvider", d.get("identity_provider", {}))),
            user_id_claim=d.get("userIDClaim", d.get("user_id_claim", "")),
            allowed_domains=d.get("allowedDomains", d.get("allowed_domains", [])),
        )


@dataclass
class IdentityProvider:
    name: str = ""
    namespace: str = ""
    spec: IdentityProviderSpec = field(default_factory=IdentityProviderSpec)

    @classmethod
    def from_dict(cls, d: dict) -> "IdentityProvider":
        return cls(
            name=d.get("name", ""),
            namespace=d.get("namespace", ""),
            spec=IdentityProviderSpec.from_dict(d.get("spec", {})),
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


@dataclass
class CatalogIndexItem:
    id: str = ""
    name: str = ""
    summary: str = ""
    description: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    latest_version: str = ""
    required_integrations: list[str] = field(default_factory=list)
    default_policies: list[str] = field(default_factory=list)
    governance_traits: list[str] = field(default_factory=list)
    complexity: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "CatalogIndexItem":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            summary=d.get("summary", ""),
            description=d.get("description", ""),
            category=d.get("category", ""),
            tags=d.get("tags", []),
            latest_version=d.get("latest_version", ""),
            required_integrations=d.get("required_integrations", []),
            default_policies=d.get("default_policies", []),
            governance_traits=d.get("governance_traits", []),
            complexity=d.get("complexity", ""),
            metadata=d.get("metadata", {}),
        )


@dataclass
class CatalogListResponse:
    generated_at: str = ""
    items: list[CatalogIndexItem] = field(default_factory=list)
    total: int = 0
    page: int = 0
    page_size: int = 0

    @classmethod
    def from_dict(cls, d: dict) -> "CatalogListResponse":
        return cls(
            generated_at=d.get("generated_at", ""),
            items=[CatalogIndexItem.from_dict(item) for item in d.get("items", [])],
            total=d.get("total", 0),
            page=d.get("page", 0),
            page_size=d.get("page_size", 0),
        )


@dataclass
class CatalogPrompt:
    title: str = ""
    content: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "CatalogPrompt":
        return cls(
            title=d.get("title", ""),
            content=d.get("content", ""),
        )


@dataclass
class CatalogDeploymentTemplate:
    workflow_ref: str = ""
    artifact_id: str = ""
    source_type: str = ""
    source_files: dict[str, str] = field(default_factory=dict)
    workflow_json: dict[str, Any] = field(default_factory=dict)
    agent_name: str = ""
    system_prompt: str = ""
    required_tools: list[str] = field(default_factory=list)
    recommended_tools: list[str] = field(default_factory=list)
    policies: list[str] = field(default_factory=list)
    access_mode: str = ""
    identity_provider: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "CatalogDeploymentTemplate":
        return cls(
            workflow_ref=d.get("workflowRef", ""),
            artifact_id=d.get("artifactId", ""),
            source_type=d.get("sourceType", ""),
            source_files=d.get("sourceFiles", {}),
            workflow_json=d.get("workflowJson", {}),
            agent_name=d.get("agentName", ""),
            system_prompt=d.get("systemPrompt", ""),
            required_tools=d.get("requiredTools", []),
            recommended_tools=d.get("recommendedTools", []),
            policies=d.get("policies", []),
            access_mode=d.get("accessMode", ""),
            identity_provider=d.get("identityProvider", ""),
        )


@dataclass
class CatalogManifest:
    id: str = ""
    version: str = ""
    name: str = ""
    summary: str = ""
    description: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    default_model: str = ""
    required_integrations: list[str] = field(default_factory=list)
    default_policies: list[str] = field(default_factory=list)
    governance_traits: list[str] = field(default_factory=list)
    access_recommendations: list[str] = field(default_factory=list)
    use_cases: list[str] = field(default_factory=list)
    prompts: list[CatalogPrompt] = field(default_factory=list)
    deployment_template: CatalogDeploymentTemplate = field(default_factory=CatalogDeploymentTemplate)
    metadata: dict[str, Any] = field(default_factory=dict)
    changelog: str = ""
    published_at: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "CatalogManifest":
        return cls(
            id=d.get("id", ""),
            version=d.get("version", ""),
            name=d.get("name", ""),
            summary=d.get("summary", ""),
            description=d.get("description", ""),
            category=d.get("category", ""),
            tags=d.get("tags", []),
            default_model=d.get("defaultModel", ""),
            required_integrations=d.get("requiredIntegrations", []),
            default_policies=d.get("defaultPolicies", []),
            governance_traits=d.get("governanceTraits", []),
            access_recommendations=d.get("accessRecommendations", []),
            use_cases=d.get("useCases", []),
            prompts=[CatalogPrompt.from_dict(item) for item in d.get("prompts", [])],
            deployment_template=CatalogDeploymentTemplate.from_dict(d.get("deploymentTemplate", {})),
            metadata=d.get("metadata", {}),
            changelog=d.get("changelog", ""),
            published_at=d.get("publishedAt", ""),
        )


@dataclass
class CatalogVersionSummary:
    version: str = ""
    published_at: str = ""
    summary: str = ""
    changelog: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "CatalogVersionSummary":
        return cls(
            version=d.get("version", ""),
            published_at=d.get("published_at", ""),
            summary=d.get("summary", ""),
            changelog=d.get("changelog", ""),
        )


@dataclass
class CatalogVersionsResponse:
    agent_id: str = ""
    versions: list[CatalogVersionSummary] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "CatalogVersionsResponse":
        return cls(
            agent_id=d.get("agent_id", ""),
            versions=[CatalogVersionSummary.from_dict(item) for item in d.get("versions", [])],
        )


@dataclass
class PolicyStatus:
    ready: bool = False
    message: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "PolicyStatus":
        return cls(
            ready=d.get("ready", False),
            message=d.get("message", ""),
        )


@dataclass
class PolicyUsage:
    name: str = ""
    namespace: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "PolicyUsage":
        return cls(
            name=d.get("name", ""),
            namespace=d.get("namespace", ""),
        )


@dataclass
class PolicyRule:
    permission: str = ""
    operations: list[str] = field(default_factory=list)
    resource: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "PolicyRule":
        return cls(
            permission=d.get("permission", ""),
            operations=d.get("operations", []),
            resource=d.get("resource", ""),
            tags=d.get("tags", []),
        )


@dataclass
class ApprovalApprovers:
    groups: list[str] = field(default_factory=list)
    match: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalApprovers":
        return cls(
            groups=d.get("groups", []),
            match=d.get("match", ""),
        )


@dataclass
class ApprovalDelivery:
    connectors: list[str] = field(default_factory=list)
    mode: str = ""
    fallback_to_ui: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalDelivery":
        return cls(
            connectors=d.get("connectors", []),
            mode=d.get("mode", ""),
            fallback_to_ui=d.get("fallbackToUI", False),
        )


@dataclass
class ApprovalRule:
    name: str = ""
    tool_ids: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    operations: list[str] = field(default_factory=list)
    resource: str = ""
    tags: list[str] = field(default_factory=list)
    approvers: ApprovalApprovers = field(default_factory=ApprovalApprovers)
    default_duration: str = ""
    delivery: ApprovalDelivery | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalRule":
        delivery = d.get("delivery")
        return cls(
            name=d.get("name", ""),
            tool_ids=d.get("toolIds", []),
            capabilities=d.get("capabilities", []),
            operations=d.get("operations", []),
            resource=d.get("resource", ""),
            tags=d.get("tags", []),
            approvers=ApprovalApprovers.from_dict(d.get("approvers", {})),
            default_duration=d.get("defaultDuration", ""),
            delivery=ApprovalDelivery.from_dict(delivery) if delivery else None,
        )


@dataclass
class PolicySpec:
    policies: list[PolicyRule] = field(default_factory=list)
    approvals: list[ApprovalRule] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "PolicySpec":
        return cls(
            policies=[PolicyRule.from_dict(item) for item in d.get("policies", [])],
            approvals=[ApprovalRule.from_dict(item) for item in d.get("approvals", [])],
        )


@dataclass
class Policy:
    name: str = ""
    namespace: str = ""
    spec: PolicySpec = field(default_factory=PolicySpec)
    status: PolicyStatus = field(default_factory=PolicyStatus)
    used_by: list[PolicyUsage] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Policy":
        return cls(
            name=d.get("name", ""),
            namespace=d.get("namespace", ""),
            spec=PolicySpec.from_dict(d.get("spec", {})),
            status=PolicyStatus.from_dict(d.get("status", {})),
            used_by=[PolicyUsage.from_dict(item) for item in d.get("used_by", [])],
        )


@dataclass
class ApprovalConnector:
    id: str = ""
    name: str = ""
    type: str = ""
    endpoint: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    enabled: bool = False
    timeout_seconds: int = 0
    slack_security_mode: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalConnector":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            type=d.get("type", ""),
            endpoint=d.get("endpoint", ""),
            headers=d.get("headers", {}),
            enabled=d.get("enabled", False),
            timeout_seconds=d.get("timeout_seconds", 0),
            slack_security_mode=d.get("slack_security_mode", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )


@dataclass
class ApprovalConnectorTestCheck:
    id: str = ""
    label: str = ""
    status: str = ""
    message: str = ""
    duration_ms: int = 0

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalConnectorTestCheck":
        return cls(
            id=d.get("id", ""),
            label=d.get("label", ""),
            status=d.get("status", ""),
            message=d.get("message", ""),
            duration_ms=d.get("duration_ms", 0),
        )


@dataclass
class ApprovalConnectorTestResult:
    status: str = ""
    connector_type: str = ""
    endpoint: str = ""
    checks: list[ApprovalConnectorTestCheck] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalConnectorTestResult":
        return cls(
            status=d.get("status", ""),
            connector_type=d.get("connector_type", ""),
            endpoint=d.get("endpoint", ""),
            checks=[ApprovalConnectorTestCheck.from_dict(item) for item in d.get("checks", [])],
        )


@dataclass
class ApprovalConnectorDefaults:
    default_delivery_mode: str = ""
    default_fallback_to_ui: bool = False
    default_timeout_seconds: int = 0
    min_timeout_seconds: int = 0
    max_timeout_seconds: int = 0

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalConnectorDefaults":
        return cls(
            default_delivery_mode=d.get("default_delivery_mode", ""),
            default_fallback_to_ui=d.get("default_fallback_to_ui", False),
            default_timeout_seconds=d.get("default_timeout_seconds", 0),
            min_timeout_seconds=d.get("min_timeout_seconds", 0),
            max_timeout_seconds=d.get("max_timeout_seconds", 0),
        )


@dataclass
class ApprovalConnectorActivity:
    id: str = ""
    timestamp: str = ""
    event: str = ""
    connector_id: str = ""
    connector_name: str = ""
    request_id: str = ""
    action_id: str = ""
    run_id: str = ""
    decision: str = ""
    approver_id: str = ""
    status_code: int = 0
    duration_ms: int = 0
    message: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalConnectorActivity":
        return cls(
            id=d.get("id", ""),
            timestamp=d.get("timestamp", ""),
            event=d.get("event", ""),
            connector_id=d.get("connector_id", ""),
            connector_name=d.get("connector_name", ""),
            request_id=d.get("request_id", ""),
            action_id=d.get("action_id", ""),
            run_id=d.get("run_id", ""),
            decision=d.get("decision", ""),
            approver_id=d.get("approver_id", ""),
            status_code=d.get("status_code", 0),
            duration_ms=d.get("duration_ms", 0),
            message=d.get("message", ""),
        )
