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
        r = Run.from_dict({"id": "run-1", "agent": "agent1", "status": "COMPLETED"})
        self.assertEqual(r.id, "run-1")
        self.assertEqual(r.status, "COMPLETED")


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


if __name__ == "__main__":
    unittest.main()
