"""Tests for runagents.agent."""

import os
import unittest
from unittest import mock

from runagents.agent import Agent, ToolNotConfigured, tool


class TestAgentInit(unittest.TestCase):
    def test_defaults(self):
        a = Agent()
        self.assertEqual(a.system_prompt, os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant."))
        self.assertEqual(a.model, os.environ.get("LLM_MODEL", "gpt-4o-mini"))

    def test_reads_tool_urls(self):
        env = {"TOOL_URL_ECHO_TOOL": "http://echo:8080", "TOOL_URL_STRIPE": "http://stripe:443"}
        with mock.patch.dict(os.environ, env):
            a = Agent()
        self.assertEqual(a.tool_urls["echo-tool"], "http://echo:8080")
        self.assertEqual(a.tool_urls["stripe"], "http://stripe:443")

    def test_call_tool_missing_raises(self):
        a = Agent()
        a.tool_urls = {}
        with self.assertRaises(ToolNotConfigured):
            a.call_tool("nonexistent")

    def test_tool_not_configured_is_still_a_key_error(self):
        a = Agent()
        a.tool_urls = {}
        with self.assertRaises(KeyError):
            a.call_tool("nonexistent")

    def test_has_tool_and_available_tools(self):
        env = {"TOOL_URL_ECHO_TOOL": "http://echo:8080", "TOOL_URL_STRIPE": "http://stripe:443"}
        with mock.patch.dict(os.environ, env):
            a = Agent()
        self.assertTrue(a.has_tool("echo-tool"))
        self.assertFalse(a.has_tool("calendar"))
        self.assertEqual(a.available_tools(), ["echo-tool", "stripe"])


class TestToolDecorator(unittest.TestCase):
    def test_bare_decorator(self):
        @tool
        def my_calculator(expr: str) -> str:
            """Evaluate an expression."""
            return str(eval(expr))

        self.assertEqual(my_calculator.tool_name, "my-calculator")
        self.assertEqual(my_calculator.tool_description, "Evaluate an expression.")
        self.assertEqual(my_calculator("1+1"), "2")

    def test_parameterized_decorator(self):
        @tool(name="weather-api", description="Get weather data")
        def weather(city: str) -> dict:
            return {"city": city, "temp": 72}

        self.assertEqual(weather.tool_name, "weather-api")
        self.assertEqual(weather.tool_description, "Get weather data")
        self.assertEqual(weather("NYC")["city"], "NYC")

    def test_preserves_function_name(self):
        @tool
        def hello():
            pass

        self.assertEqual(hello.__name__, "hello")


class TestToolDecoratorWithNoDocstring(unittest.TestCase):
    def test_no_docstring(self):
        @tool
        def bare_func():
            pass

        self.assertEqual(bare_func.tool_name, "bare-func")
        self.assertEqual(bare_func.tool_description, "")


if __name__ == "__main__":
    unittest.main()
