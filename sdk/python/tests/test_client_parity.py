"""Parity-focused tests for new public SDK surfaces."""

import os
import unittest
from unittest import mock

from runagents.client import Client
from runagents.types import (
    ActionPlanApplyResponse,
    ActionPlanValidationResponse,
    AgentConfig,
    AgentConfigLLM,
    ModelSpendResponse,
)


class TestPublicSurfaceParity(unittest.TestCase):
    def _client(self) -> Client:
        with mock.patch.dict(os.environ, {"RUNAGENTS_ENDPOINT": "http://test:8092"}, clear=True):
            return Client()

    def test_actions_validate_returns_typed_response(self):
        client = self._client()
        with mock.patch.object(
            client,
            "post",
            return_value={
                "plan_id": "plan-1",
                "namespace": "agent-system",
                "valid": True,
                "results": [{"id": "step-1", "type": "tool.upsert", "valid": True}],
            },
        ) as mock_post:
            result = client.actions.validate({"actions": [{"type": "tool.upsert", "idempotency_key": "k1"}]})

        self.assertIsInstance(result, ActionPlanValidationResponse)
        self.assertTrue(result.valid)
        self.assertEqual(result.results[0].type, "tool.upsert")
        mock_post.assert_called_once_with(
            "/actions/validate",
            {"actions": [{"type": "tool.upsert", "idempotency_key": "k1"}]},
        )

    def test_actions_apply_returns_typed_response(self):
        client = self._client()
        with mock.patch.object(
            client,
            "post",
            return_value={
                "plan_id": "plan-2",
                "namespace": "agent-system",
                "applied": True,
                "applied_count": 1,
                "failed_count": 0,
                "results": [{"id": "step-1", "type": "starter_kit.seed", "status": "applied"}],
            },
        ) as mock_post:
            result = client.actions.apply({"actions": [{"type": "starter_kit.seed", "idempotency_key": "k2"}]})

        self.assertIsInstance(result, ActionPlanApplyResponse)
        self.assertTrue(result.applied)
        self.assertEqual(result.results[0].status, "applied")
        mock_post.assert_called_once_with(
            "/actions/apply",
            {"actions": [{"type": "starter_kit.seed", "idempotency_key": "k2"}]},
        )

    def test_model_spend_get_returns_typed_response(self):
        client = self._client()
        with mock.patch.object(
            client,
            "get",
            return_value={
                "summary": {
                    "total_estimated_spend_usd": 42,
                    "total_budget_usd": 50,
                    "remaining_budget_usd": 8,
                    "budgeted_model_count": 1,
                },
                "warnings": [
                    {
                        "agent_name": "expense-bot",
                        "label": "Chat model",
                        "model": "gpt-4o",
                        "monthly_budget_usd": 50,
                        "estimated_spend_usd": 42,
                    }
                ],
                "top_models": [],
            },
        ) as mock_get:
            spend = client.model_spend.get()

        self.assertIsInstance(spend, ModelSpendResponse)
        self.assertEqual(spend.summary.total_estimated_spend_usd, 42)
        self.assertEqual(spend.warnings[0].agent_name, "expense-bot")
        mock_get.assert_called_once_with("/model-spend")

    def test_agent_config_get_returns_budgets_and_usage(self):
        client = self._client()
        with mock.patch.object(
            client,
            "get",
            return_value={
                "agent_name": "expense-bot",
                "namespace": "default",
                "llm_configs": [
                    {"role": "chat", "provider": "openai", "model": "gpt-4o", "monthly_budget_usd": 50}
                ],
                "model_usage": [
                    {"label": "Chat model", "model": "gpt-4o", "estimated_spend_usd": 42}
                ],
            },
        ) as mock_get:
            cfg = client.agents.get_config("expense-bot")

        self.assertIsInstance(cfg, AgentConfig)
        self.assertEqual(cfg.llm_configs[0].monthly_budget_usd, 50)
        self.assertEqual(cfg.model_usage[0].estimated_spend_usd, 42)
        mock_get.assert_called_once_with("/agents/expense-bot/config")

    def test_agent_config_update_accepts_typed_llm_configs(self):
        client = self._client()
        with mock.patch.object(
            client,
            "put",
            return_value={
                "agent_name": "expense-bot",
                "llm_configs": [
                    {"role": "chat", "provider": "openai", "model": "gpt-4o", "monthly_budget_usd": 75}
                ],
            },
        ) as mock_put:
            cfg = client.agents.update_config(
                "expense-bot",
                llm_configs=[AgentConfigLLM(role="chat", provider="openai", model="gpt-4o", monthly_budget_usd=75)],
            )

        self.assertIsInstance(cfg, AgentConfig)
        self.assertEqual(cfg.llm_configs[0].monthly_budget_usd, 75)
        mock_put.assert_called_once_with(
            "/agents/expense-bot/config",
            {"llm_configs": [{"role": "chat", "provider": "openai", "model": "gpt-4o", "monthly_budget_usd": 75}]},
        )

    def test_agent_config_update_requires_payload(self):
        client = self._client()
        with self.assertRaises(ValueError):
            client.agents.update_config("expense-bot")


if __name__ == "__main__":
    unittest.main()
