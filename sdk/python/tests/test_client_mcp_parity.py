"""Tests for newer Python client resources used by the MCP server."""

import unittest
from unittest import mock

from runagents.client import (
    APIError,
    ApprovalConnector,
    CatalogManifest,
    Client,
    _build_catalog_deploy_payload,
    _normalize_policy_apply_request,
)


class TestClientResourceProperties(unittest.TestCase):
    def test_has_new_resource_properties(self):
        c = Client(endpoint="http://example.com")
        self.assertTrue(hasattr(c, "catalog"))
        self.assertTrue(hasattr(c, "policies"))
        self.assertTrue(hasattr(c, "approval_connectors"))


class TestCatalogResource(unittest.TestCase):
    def test_list_uses_expected_query_shape(self):
        c = Client(endpoint="http://example.com")
        payload = {"items": [], "total": 0, "page": 2, "page_size": 50}
        with mock.patch.object(c, "get_with_query", return_value=payload) as mocked:
            c.catalog.list(
                search="google",
                categories=["Enterprise Productivity"],
                tags=["Gmail"],
                integrations=["calendar"],
                governance=["approval-ready"],
                page=2,
                page_size=50,
            )
        mocked.assert_called_once_with(
            "/api/catalog",
            {
                "search": "google",
                "category": ["Enterprise Productivity"],
                "tag": ["Gmail"],
                "integration": ["calendar"],
                "governance": ["approval-ready"],
                "page": "2",
                "page_size": "50",
            },
        )

    def test_get_supports_version_query(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(c, "get", return_value={"id": "google-agent", "version": "1.2.0"}) as mocked:
            manifest = c.catalog.get("google-agent", version="1.2.0")
        mocked.assert_called_once_with("/api/catalog/google-agent?version=1.2.0")
        self.assertEqual(manifest.id, "google-agent")
        self.assertEqual(manifest.version, "1.2.0")

    def test_build_catalog_deploy_payload_uses_manifest_defaults(self):
        manifest = CatalogManifest.from_dict(
            {
                "id": "google-workspace-assistant-agent",
                "defaultModel": "gpt-4.1",
                "deploymentTemplate": {
                    "agentName": "google-workspace-assistant-agent",
                    "systemPrompt": "You are a Google Workspace assistant.",
                    "requiredTools": ["email", "calendar"],
                    "policies": ["workspace-write-approval"],
                    "identityProvider": "google-oidc",
                    "sourceFiles": {"src/agent.py": "print('hello')"},
                },
            }
        )
        payload = _build_catalog_deploy_payload(manifest)
        self.assertEqual(payload["agent_name"], "google-workspace-assistant-agent")
        self.assertEqual(payload["required_tools"], ["email", "calendar"])
        self.assertEqual(payload["policies"], ["workspace-write-approval"])
        self.assertEqual(payload["identity_provider"], "google-oidc")
        self.assertEqual(
            payload["llm_configs"],
            [{"provider": "openai", "model": "gpt-4.1", "role": "default"}],
        )


class TestPolicyResource(unittest.TestCase):
    def test_normalize_policy_apply_request_supports_raw_spec_override(self):
        request = _normalize_policy_apply_request(
            {"policies": [{"permission": "allow", "operations": ["GET"]}]},
            override_name="workspace-read",
        )
        self.assertEqual(request["name"], "workspace-read")
        self.assertIn("policies", request["spec"])

    def test_apply_posts_when_policy_does_not_exist(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(c, "get", side_effect=APIError(404, "not found")) as mocked_get, mock.patch.object(
            c,
            "post",
            return_value={"name": "workspace-read", "spec": {"policies": [{"permission": "allow"}]}},
        ) as mocked_post:
            policy = c.policies.apply(
                {"policies": [{"permission": "allow", "operations": ["GET"]}]},
                name="workspace-read",
            )
        mocked_get.assert_called_once_with("/api/policies/workspace-read")
        mocked_post.assert_called_once()
        self.assertEqual(policy.name, "workspace-read")

    def test_translate_returns_rules(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(
            c,
            "post",
            return_value={"rules": [{"permission": "approval_required", "operations": ["POST"]}]},
        ):
            rules = c.policies.translate("Require approval for writes")
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].permission, "approval_required")


class TestApprovalConnectorResource(unittest.TestCase):
    def test_apply_patches_existing_connector_by_name(self):
        c = Client(endpoint="http://example.com")
        existing = ApprovalConnector(id="ac_123", name="secops-slack", type="slack", endpoint="C123")
        with mock.patch.object(c.approval_connectors, "list", return_value=[existing]), mock.patch.object(
            c,
            "patch",
            return_value={"id": "ac_123", "name": "secops-slack", "type": "slack", "endpoint": "C456"},
        ) as mocked_patch:
            connector = c.approval_connectors.apply({"name": "secops-slack", "endpoint": "C456"})
        mocked_patch.assert_called_once_with(
            "/api/settings/approval-connectors/ac_123",
            {"name": "secops-slack", "endpoint": "C456"},
        )
        self.assertEqual(connector.id, "ac_123")
        self.assertEqual(connector.endpoint, "C456")

    def test_test_uses_live_connector_configuration(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(
            c.approval_connectors,
            "get",
            return_value=ApprovalConnector(
                id="ac_123",
                name="secops-slack",
                type="slack",
                endpoint="C123",
                headers={"X-Slack-Bot-Token": "xoxb-1"},
                timeout_seconds=30,
                slack_security_mode="compat",
            ),
        ), mock.patch.object(
            c,
            "post",
            return_value={"status": "healthy", "connector_type": "slack", "endpoint": "C123", "checks": []},
        ) as mocked_post:
            result = c.approval_connectors.test("ac_123")
        mocked_post.assert_called_once_with(
            "/api/settings/approval-connectors/test",
            {
                "type": "slack",
                "endpoint": "C123",
                "headers": {"X-Slack-Bot-Token": "xoxb-1"},
                "timeout_seconds": 30,
                "slack_security_mode": "compat",
            },
        )
        self.assertEqual(result.status, "healthy")


if __name__ == "__main__":
    unittest.main()
