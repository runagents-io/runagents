"""Hello World agent -- uses the built-in echo tool and LLM gateway.

This is a Tier 1 agent: no custom handler or framework imports.
The platform's built-in runtime handles tool calling automatically.

Deploy:
    runagents deploy --files agent.py --name hello-world
"""
import os
import json
import urllib.request

TOOL_URL = os.environ.get("TOOL_URL_ECHO_TOOL", "http://echo-tool:8080")
LLM_URL = os.environ.get("LLM_GATEWAY_URL", "http://llm-gateway:8080/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def call_echo_tool(message: str) -> dict:
    """Send a message to the echo tool and get it echoed back."""
    req = urllib.request.Request(
        f"{TOOL_URL}/echo",
        data=json.dumps({"message": message}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def ask_llm(prompt: str) -> str:
    """Send a chat completion request via the LLM gateway."""
    body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        LLM_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    echo_result = call_echo_tool("Hello from my first agent!")
    print(f"Echo tool replied: {echo_result['reply']}")

    answer = ask_llm("Summarize what RunAgents does in one sentence.")
    print(f"LLM says: {answer}")
