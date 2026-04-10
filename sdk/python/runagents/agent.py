"""Agent SDK for writing RunAgents agents.

Provides a high-level Agent class that reads operator-injected env vars
and exposes ``call_tool()`` and ``chat()`` helpers. Stdlib only.

Usage::

    from runagents import Agent

    agent = Agent()
    result = agent.chat("What is 2+2?", tools=[...])
"""

from __future__ import annotations

import json
import os
import functools
from typing import Any, Callable


class ToolNotConfigured(KeyError):
    """Raised when code asks for a managed tool that is not bound for this agent."""

    def __init__(self, name: str, env_key: str):
        self.tool_name = name
        self.env_key = env_key
        super().__init__(f"Tool {name!r} not found. Set {env_key} or check requiredTools.")


class Agent:
    """High-level agent helper that reads operator-injected env vars.

    Attributes:
        system_prompt: The agent's system prompt.
        model: LLM model name (e.g. ``gpt-4o-mini``).
        llm_gateway_url: URL for the LLM gateway chat completions endpoint.
        tool_urls: Mapping of tool name → base URL.
    """

    def __init__(self):
        self.system_prompt = os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant.")
        self.model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.llm_gateway_url = os.environ.get(
            "LLM_GATEWAY_URL",
            "http://llm-gateway.agent-system.svc:8080/v1/chat/completions",
        )
        self.tool_urls: dict[str, str] = {}
        for key, val in os.environ.items():
            if key.startswith("TOOL_URL_"):
                name = key[len("TOOL_URL_"):].lower().replace("_", "-")
                self.tool_urls[name] = val

    def has_tool(self, name: str) -> bool:
        """Return True when a RunAgents-managed tool is bound for this agent."""
        return name in self.tool_urls

    def available_tools(self) -> list[str]:
        """Return the sorted list of bound RunAgents-managed tool names."""
        return sorted(self.tool_urls)

    def call_tool(
        self,
        name: str,
        path: str = "/",
        payload: dict | None = None,
        method: str = "POST",
    ) -> dict:
        """Call a platform tool by name.

        The Istio mesh handles auth and policy — this just makes the HTTP call.

        Args:
            name: Tool name (must be in ``self.tool_urls``).
            path: HTTP path on the tool (default ``/``).
            payload: JSON body (for POST/PUT/PATCH).
            method: HTTP method.

        Returns:
            Parsed JSON response.

        Raises:
            ToolNotConfigured: If tool name is not found in env vars.
        """
        from runagents.runtime import execute_tool_call

        base = self.tool_urls.get(name)
        if base is None:
            env_key = "TOOL_URL_" + name.upper().replace("-", "_")
            raise ToolNotConfigured(name, env_key)

        url = base.rstrip("/") + path
        body = json.dumps(payload) if payload else None
        result_str = execute_tool_call(
            method,
            url,
            body=body,
            tool_name=name,
            function_name=name,
            source="agent_sdk",
        )
        try:
            return json.loads(result_str)
        except (json.JSONDecodeError, TypeError):
            return {"raw": result_str}

    def chat(
        self,
        message: str,
        tools: list[dict] | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        """Send a chat completion request through the LLM gateway.

        Args:
            message: User message.
            tools: OpenAI-format tool definitions (optional).
            history: Prior conversation messages (optional).

        Returns:
            Full OpenAI-format response dict.
        """
        from runagents.runtime import call_llm

        messages = list(history) if history else []
        messages.append({"role": "user", "content": message})

        return call_llm(
            messages,
            gateway_url=self.llm_gateway_url,
            model=self.model,
            system_prompt=self.system_prompt if not history else None,
            tools=tools,
        )


def tool(fn: Callable | None = None, *, name: str | None = None, description: str = "") -> Any:
    """Decorator to mark a function as a tool handler.

    The decorated function gains ``.tool_name`` and ``.tool_description``
    attributes for discovery by frameworks.

    Usage::

        @tool
        def calculator(expression: str) -> str:
            return str(eval(expression))

        @tool(name="weather-lookup", description="Get current weather")
        def weather(city: str) -> dict:
            ...
    """
    def decorator(f: Callable) -> Callable:
        f.tool_name = name or f.__name__.replace("_", "-")  # type: ignore[attr-defined]
        f.tool_description = description or (f.__doc__ or "").strip().split("\n")[0]  # type: ignore[attr-defined]

        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        wrapper.tool_name = f.tool_name  # type: ignore[attr-defined]
        wrapper.tool_description = f.tool_description  # type: ignore[attr-defined]
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator
