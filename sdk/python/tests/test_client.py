"""Tests for runagents.client."""

import json
import os
import unittest
from unittest import mock

from runagents.client import Client, APIError


class TestClientHeaders(unittest.TestCase):
    def test_basic_headers(self):
        with mock.patch.dict(os.environ, {"RUNAGENTS_ENDPOINT": "http://test:8092"}, clear=True):
            c = Client(api_key="sk-test", namespace="prod")
        h = c._headers()
        self.assertEqual(h["Authorization"], "Bearer sk-test")
        self.assertEqual(h["X-Workspace-Namespace"], "prod")
        self.assertNotIn("X-RunAgents-API-Key", h)

    def test_workspace_key_headers(self):
        with mock.patch.dict(os.environ, {"RUNAGENTS_ENDPOINT": "http://test:8092"}, clear=True):
            c = Client(api_key="ra_ws_abc123", namespace="trial-1")
        h = c._headers()
        self.assertEqual(h["Authorization"], "Bearer ra_ws_abc123")
        self.assertEqual(h["X-RunAgents-API-Key"], "ra_ws_abc123")

    def test_no_auth(self):
        with mock.patch.dict(os.environ, {"RUNAGENTS_ENDPOINT": "http://test:8092"}, clear=True):
            c = Client(api_key="", namespace="")
        h = c._headers()
        self.assertNotIn("Authorization", h)
        self.assertNotIn("X-Workspace-Namespace", h)


class TestClientRepr(unittest.TestCase):
    def test_repr(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            c = Client(endpoint="http://example.com", namespace="ns")
        self.assertIn("example.com", repr(c))
        self.assertIn("ns", repr(c))


class TestClientResources(unittest.TestCase):
    def test_has_resource_properties(self):
        with mock.patch.dict(os.environ, {"RUNAGENTS_ENDPOINT": "http://test:8092"}, clear=True):
            c = Client()
        self.assertTrue(hasattr(c, "agents"))
        self.assertTrue(hasattr(c, "tools"))
        self.assertTrue(hasattr(c, "models"))
        self.assertTrue(hasattr(c, "runs"))
        self.assertTrue(hasattr(c, "approvals"))


class TestAPIError(unittest.TestCase):
    def test_error_attrs(self):
        e = APIError(404, "not found")
        self.assertEqual(e.status, 404)
        self.assertEqual(e.detail, "not found")
        self.assertIn("404", str(e))


if __name__ == "__main__":
    unittest.main()
