"""OpenAI SDK agent -- auto-routes through the platform LLM Gateway.

The platform sets OPENAI_BASE_URL and OPENAI_API_KEY automatically,
so openai.OpenAI() works without any configuration. All LLM calls
transparently route through the LLM Gateway and Istio mesh.

Deploy:
    runagents deploy --files agent.py --name openai-agent
"""
import os
import json
import openai
import requests

# No configuration needed! The platform sets OPENAI_BASE_URL and OPENAI_API_KEY
# automatically so this client routes through the LLM Gateway.
client = openai.OpenAI()
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def handler(request, context):
    message = request["message"]
    history = request.get("history", [])

    messages = [{"role": "system", "content": context.system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    # Define tools if weather service is available
    tools = []
    if "weather" in context.tools:
        tools.append({
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"],
                },
            },
        })

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools if tools else openai.NOT_GIVEN,
    )

    choice = response.choices[0]

    # Handle tool calls
    if choice.message.tool_calls:
        messages.append(choice.message)
        for tc in choice.message.tool_calls:
            args = json.loads(tc.function.arguments)
            result = _execute_tool(tc.function.name, args, context)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

        # Get final response after tool execution
        response = client.chat.completions.create(model=MODEL, messages=messages)
        return {"response": response.choices[0].message.content}

    return {"response": choice.message.content}


def _execute_tool(name, args, context):
    """Execute a tool call by name."""
    if name == "get_weather":
        url = context.tools.get("weather", "")
        resp = requests.post(f"{url}/weather/lookup", json={"city": args["city"]})
        return resp.json()
    return {"error": f"Unknown tool: {name}"}
