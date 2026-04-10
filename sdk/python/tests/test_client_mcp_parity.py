"""Tests for newer Python client resources used by the MCP server."""

import unittest
from unittest import mock

from runagents.client import (
    APIError,
    ApprovalConnector,
    CatalogManifest,
    Client,
    Event,
    Run,
    _build_catalog_deploy_payload,
    _build_agent_deploy_payload,
    _build_approval_decision,
    _normalize_identity_provider_apply_request,
    _normalize_policy_apply_request,
)


class TestClientResourceProperties(unittest.TestCase):
    def test_has_new_resource_properties(self):
        c = Client(endpoint="http://example.com")
        self.assertTrue(hasattr(c, "catalog"))
        self.assertTrue(hasattr(c, "policies"))
        self.assertTrue(hasattr(c, "approval_connectors"))
        self.assertTrue(hasattr(c, "identity_providers"))


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


class TestIdentityProviderResource(unittest.TestCase):
    def test_normalize_identity_provider_apply_request_supports_raw_spec(self):
        request = _normalize_identity_provider_apply_request(
            {
                "host": "portal.example.com",
                "identityProvider": {
                    "issuer": "https://accounts.google.com",
                    "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
                },
                "userIDClaim": "email",
            },
            override_name="google-oidc",
        )
        self.assertEqual(request["name"], "google-oidc")
        self.assertEqual(request["spec"]["host"], "portal.example.com")

    def test_apply_posts_normalized_document(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(
            c,
            "post",
            return_value={"name": "google-oidc", "namespace": "default", "spec": {"host": "portal.example.com"}},
        ) as mocked_post:
            provider = c.identity_providers.apply(
                {
                    "host": "portal.example.com",
                    "identityProvider": {
                        "issuer": "https://accounts.google.com",
                        "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
                    },
                    "userIDClaim": "email",
                },
                name="google-oidc",
            )
        mocked_post.assert_called_once()
        self.assertEqual(provider.name, "google-oidc")


class TestRunResource(unittest.TestCase):
    def test_list_applies_client_side_user_and_conversation_filters(self):
        c = Client(endpoint="http://example.com")
        payload = [
            {
                "id": "run-1",
                "agent_id": "workspace",
                "user_id": "alice@example.com",
                "conversation_id": "conv-a",
                "updated_at": "2026-04-09T10:00:00Z",
            },
            {
                "id": "run-2",
                "agent_id": "workspace",
                "user_id": "alice@example.com",
                "conversation_id": "conv-a",
                "updated_at": "2026-04-09T10:05:00Z",
            },
            {
                "id": "run-3",
                "agent_id": "workspace",
                "user_id": "bob@example.com",
                "conversation_id": "conv-b",
                "updated_at": "2026-04-09T10:04:00Z",
            },
        ]
        with mock.patch.object(c, "get_with_query", return_value=payload) as mocked:
            runs = c.runs.list(agent="workspace", user="alice@example.com", conversation="conv-a", limit=1)
        mocked.assert_called_once_with("/runs", {"agent_id": "workspace"})
        self.assertEqual([run.id for run in runs], ["run-2"])

    def test_timeline_summarizes_approval_required(self):
        c = Client(endpoint="http://example.com")
        event = {
            "event_id": "evt-1",
            "seq": 2,
            "type": "APPROVAL_REQUIRED",
            "data": {"tool_id": "calendar", "capability": "create-event"},
            "timestamp": "2026-04-09T10:01:00Z",
        }
        with mock.patch.object(
            c.runs,
            "get",
            return_value=Run.from_dict({"id": "run-1", "status": "PAUSED_APPROVAL", "updated_at": "2026-04-09T10:00:00Z"}),
        ), mock.patch.object(
            c.runs,
            "events",
            return_value=[Event.from_dict(event)],
        ):
            timeline = c.runs.timeline("run-1")
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0].summary, "Approval required for calendar (create-event)")

    def test_export_includes_run_events_and_timeline(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(
            c.runs,
            "get",
            return_value=Run.from_dict({"id": "run-1", "status": "COMPLETED", "updated_at": "2026-04-09T10:05:00Z"}),
        ), mock.patch.object(
            c.runs,
            "events",
            return_value=[Event.from_dict({"event_id": "evt-1", "seq": 1, "type": "COMPLETED", "timestamp": "2026-04-09T10:05:00Z"})],
        ):
            export = c.runs.export("run-1")
        self.assertEqual(export.run.id, "run-1")
        self.assertEqual(len(export.events), 1)
        self.assertEqual(export.timeline[0].summary, "Run completed successfully")

    def test_wait_returns_terminal_run(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(
            c.runs,
            "get",
            side_effect=[
                Run.from_dict({"id": "run-1", "status": "RUNNING"}),
                Run.from_dict({"id": "run-1", "status": "COMPLETED"}),
            ],
        ), mock.patch("runagents.client.time.sleep", return_value=None):
            run = c.runs.wait("run-1", timeout_seconds=1, interval_seconds=0)
        self.assertEqual(run.status, "COMPLETED")


class TestDeployAndApprovalParity(unittest.TestCase):
    def test_build_agent_deploy_payload_supports_draft_and_governance(self):
        payload = _build_agent_deploy_payload(
            name="billing-agent",
            draft_id="draft_billing_v2",
            policies=["billing-write-approval"],
            identity_provider="google-oidc",
        )
        self.assertEqual(payload["draft_id"], "draft_billing_v2")
        self.assertEqual(payload["policies"], ["billing-write-approval"])
        self.assertEqual(payload["identity_provider"], "google-oidc")

    def test_build_agent_deploy_payload_rejects_framework_without_source(self):
        with self.assertRaisesRegex(ValueError, "framework can only be used with source_files"):
            _build_agent_deploy_payload(name="artifact-agent", artifact_id="art_123", framework="langgraph")

    def test_build_approval_decision_normalizes_window_alias(self):
        decision = _build_approval_decision(scope="window", duration="4h")
        self.assertEqual(decision, {"scope": "agent_user_ttl", "duration": "4h"})

    def test_approve_posts_scope_and_duration(self):
        c = Client(endpoint="http://example.com")
        with mock.patch.object(c, "post", return_value={"status": "approved"}) as mocked_post:
            c.approvals.approve("req_123", scope="run", duration="")
        mocked_post.assert_called_once_with(
            "/governance/requests/req_123/approve",
            {"scope": "run", "duration": ""},
        )


if __name__ == "__main__":
    unittest.main()
