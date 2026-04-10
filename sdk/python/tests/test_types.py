"""Tests for runagents.types."""

import unittest

from runagents.types import (
    Agent,
    Tool,
    ModelProvider,
    Run,
    Event,
    DeployResult,
    AnalysisResult,
    CatalogManifest,
    Policy,
    ApprovalConnectorTestResult,
    IdentityProvider,
)


class TestAgentFromDict(unittest.TestCase):
    def test_flat_dict(self):
        a = Agent.from_dict({"name": "test", "namespace": "default", "status": "Running"})
        self.assertEqual(a.name, "test")
        self.assertEqual(a.namespace, "default")
        self.assertEqual(a.status, "Running")

    def test_k8s_style_dict(self):
        a = Agent.from_dict({
            "metadata": {"name": "agent1", "namespace": "prod", "creationTimestamp": "2025-01-01"},
            "spec": {"image": "agent:v1", "requiredTools": ["echo"], "systemPrompt": "Be helpful"},
            "status": {"phase": "Running"},
        })
        self.assertEqual(a.name, "agent1")
        self.assertEqual(a.namespace, "prod")
        self.assertEqual(a.status, "Running")
        self.assertEqual(a.image, "agent:v1")
        self.assertEqual(a.required_tools, ["echo"])

    def test_empty_dict(self):
        a = Agent.from_dict({})
        self.assertEqual(a.name, "")


class TestToolFromDict(unittest.TestCase):
    def test_k8s_style(self):
        t = Tool.from_dict({
            "metadata": {"name": "stripe"},
            "spec": {
                "description": "Stripe API",
                "connection": {"baseUrl": "https://api.stripe.com", "authentication": {"type": "APIKey"}},
                "topology": "External",
                "accessMode": "Open",
                "capabilities": [{"name": "charge", "method": "POST", "path": "/v1/charges"}],
            },
        })
        self.assertEqual(t.name, "stripe")
        self.assertEqual(t.base_url, "https://api.stripe.com")
        self.assertEqual(t.auth_type, "APIKey")
        self.assertEqual(len(t.capabilities), 1)


class TestRunFromDict(unittest.TestCase):
    def test_basic(self):
        r = Run.from_dict(
            {
                "id": "run-1",
                "agent_id": "agent1",
                "conversation_id": "conv-1",
                "user_id": "alice@example.com",
                "status": "COMPLETED",
            }
        )
        self.assertEqual(r.id, "run-1")
        self.assertEqual(r.agent_id, "agent1")
        self.assertEqual(r.agent, "agent1")
        self.assertEqual(r.user_id, "alice@example.com")
        self.assertEqual(r.status, "COMPLETED")


class TestEventFromDict(unittest.TestCase):
    def test_modern_shape(self):
        e = Event.from_dict(
            {
                "event_id": "evt-1",
                "run_id": "run-1",
                "seq": 3,
                "type": "APPROVAL_REQUIRED",
                "actor": "alice@example.com",
                "timestamp": "2026-04-09T10:01:00Z",
            }
        )
        self.assertEqual(e.event_id, "evt-1")
        self.assertEqual(e.id, "evt-1")
        self.assertEqual(e.seq, 3)
        self.assertEqual(e.sequence, 3)
        self.assertEqual(e.created_at, "2026-04-09T10:01:00Z")


class TestDeployResultFromDict(unittest.TestCase):
    def test_basic(self):
        d = DeployResult.from_dict({"agent_name": "test", "status": "created", "tools_created": ["echo"]})
        self.assertEqual(d.agent_name, "test")
        self.assertEqual(d.tools_created, ["echo"])


class TestAnalysisResultFromDict(unittest.TestCase):
    def test_basic(self):
        a = AnalysisResult.from_dict({
            "id": "abc",
            "framework": "langchain",
            "runtime_family": "langchain",
            "adapter": "langchain",
            "tools": [{"name": "stripe"}],
            "entry_point": "agent.py",
        })
        self.assertEqual(a.id, "abc")
        self.assertEqual(a.framework, "langchain")
        self.assertEqual(a.runtime_family, "langchain")
        self.assertEqual(a.adapter, "langchain")
        self.assertEqual(len(a.tools), 1)
        self.assertEqual(a.entry_point, "agent.py")


class TestCatalogManifestFromDict(unittest.TestCase):
    def test_manifest(self):
        manifest = CatalogManifest.from_dict(
            {
                "id": "google-workspace-assistant-agent",
                "version": "1.2.0",
                "name": "Google Workspace Assistant",
                "deploymentTemplate": {
                    "agentName": "google-workspace-assistant-agent",
                    "requiredTools": ["email", "calendar"],
                },
            }
        )
        self.assertEqual(manifest.id, "google-workspace-assistant-agent")
        self.assertEqual(manifest.version, "1.2.0")
        self.assertEqual(manifest.deployment_template.agent_name, "google-workspace-assistant-agent")
        self.assertEqual(manifest.deployment_template.required_tools, ["email", "calendar"])


class TestPolicyFromDict(unittest.TestCase):
    def test_policy(self):
        policy = Policy.from_dict(
            {
                "name": "workspace-write-approval",
                "namespace": "default",
                "spec": {
                    "policies": [{"permission": "allow", "operations": ["GET"]}],
                    "approvals": [
                        {
                            "name": "workspace-writes",
                            "approvers": {"groups": ["self-approvers"]},
                            "defaultDuration": "4h",
                        }
                    ],
                },
                "status": {"ready": True},
            }
        )
        self.assertEqual(policy.name, "workspace-write-approval")
        self.assertEqual(len(policy.spec.policies), 1)
        self.assertEqual(len(policy.spec.approvals), 1)
        self.assertTrue(policy.status.ready)


class TestApprovalConnectorTestResultFromDict(unittest.TestCase):
    def test_result(self):
        result = ApprovalConnectorTestResult.from_dict(
            {
                "status": "healthy",
                "connector_type": "webhook",
                "endpoint": "https://approvals.example.com/hook",
                "checks": [{"id": "config", "label": "Configuration", "status": "passed"}],
            }
        )
        self.assertEqual(result.status, "healthy")
        self.assertEqual(result.connector_type, "webhook")
        self.assertEqual(len(result.checks), 1)
        self.assertEqual(result.checks[0].label, "Configuration")


class TestIdentityProviderFromDict(unittest.TestCase):
    def test_provider(self):
        provider = IdentityProvider.from_dict(
            {
                "name": "google-oidc",
                "namespace": "default",
                "spec": {
                    "host": "portal.example.com",
                    "identityProvider": {
                        "issuer": "https://accounts.google.com",
                        "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
                        "audiences": ["portal.example.com"],
                    },
                    "userIDClaim": "email",
                    "allowedDomains": ["example.com"],
                },
            }
        )
        self.assertEqual(provider.name, "google-oidc")
        self.assertEqual(provider.spec.host, "portal.example.com")
        self.assertEqual(provider.spec.identity_provider.issuer, "https://accounts.google.com")
        self.assertEqual(provider.spec.user_id_claim, "email")


if __name__ == "__main__":
    unittest.main()
