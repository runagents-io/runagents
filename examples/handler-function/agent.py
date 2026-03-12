"""Custom handler agent -- full control over request processing.

This is the simplest Tier 2 pattern. Define a handler() function and
the runtime calls it for every incoming message.

The RunContext provides platform-injected tool URLs, LLM config, and
session state so you don't need to read env vars directly.

Deploy:
    runagents deploy --files agent.py --name my-handler-agent
"""
import json
import urllib.request


def handler(request, context):
    """Called by the runtime for each incoming message.

    Args:
        request: dict with "message" (str) and "history" (list)
        context: RunContext with tools, llm_url, model, system_prompt, session
    """
    message = request["message"]

    # Call a tool using platform-provided URLs
    tool_url = context.tools.get("calculator")
    if tool_url and "calculate" in message.lower():
        result = _call_tool(tool_url, "/calculate", {"a": 10, "b": 5, "op": "add"})
        return {"response": f"Calculator says: {result}"}

    # Otherwise, ask the LLM
    llm_response = _call_llm(context.llm_url, context.model, context.system_prompt, message)
    return {"response": llm_response}


def _call_tool(base_url, path, payload):
    """Make an HTTP call to a platform tool."""
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _call_llm(llm_url, model, system_prompt, message):
    """Send a chat completion request to the LLM gateway."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
    }
    req = urllib.request.Request(
        llm_url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
