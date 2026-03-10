# Writing Agents

This guide walks through five complete agent examples, from zero-code to framework-based. Each example includes a full Python file you can deploy directly.

All examples are available in the [`examples/`](https://github.com/runagents-io/runagents/tree/main/examples) directory.

---

## Example 1: Hello World (Tier 1 -- No Custom Code)

The simplest possible agent. Upload this file and the platform handles everything: tool calling, LLM communication, and response generation.

```python
"""Hello World agent -- uses the built-in echo tool."""
import os
import json
import urllib.request

TOOL_URL = os.environ.get("TOOL_URL_ECHO_TOOL", "http://echo-tool:8080")
LLM_URL = os.environ.get("LLM_GATEWAY_URL", "http://llm-gateway:8080/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def call_echo_tool(message: str) -> dict:
    req = urllib.request.Request(
        f"{TOOL_URL}/echo",
        data=json.dumps({"message": message}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def ask_llm(prompt: str) -> str:
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
```

**Deploy:**

=== "Console"
    Upload `agent.py` in the deploy wizard. The platform detects the echo tool call and LLM usage, wires them to your registered resources, and deploys using the built-in runtime image.

=== "CLI"
    ```bash
    runagents deploy --files agent.py --name hello-world
    ```

**What happens behind the scenes:**

1. The ingestion service analyzes `agent.py` and detects the echo tool + LLM usage
2. No `handler()` function or framework imports are found → **Tier 1**
3. The platform uses the pre-built runtime image (no container build needed)
4. The operator creates a ConfigMap with `TOOL_URL_ECHO_TOOL`, `LLM_GATEWAY_URL`, `TOOL_DEFINITIONS_JSON`, etc.
5. The built-in tool-calling loop handles all LLM ↔ tool interactions at runtime

---

## Example 2: Handler Function (Simplest Tier 2)

Define a `handler()` function to control exactly what your agent does. This is the simplest Tier 2 pattern.

```python
"""Custom handler agent -- full control over request processing."""
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
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _call_llm(llm_url, model, system_prompt, message):
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
```

**Deploy:**

=== "Console"
    Upload `agent.py`. The platform detects `def handler(` → Tier 2. If your code has no extra pip dependencies, it uses the pre-built runtime image. Otherwise it builds a custom image.

=== "CLI"
    ```bash
    runagents deploy --files agent.py --name my-handler-agent
    ```

**What happens behind the scenes:**

1. `def handler(` detected → **Tier 2**
2. No framework imports or custom pip requirements → uses pre-built runtime image
3. The runtime sets `USER_ENTRY_POINT=agent.py`, imports the module, and finds `handler()`
4. Every `POST /invoke` calls your `handler(request, context)` directly
5. `context.tools` is populated from `TOOL_URL_*` env vars; `context.llm_url` from `LLM_GATEWAY_URL`

---

## Example 3: OpenAI SDK Agent

Use the OpenAI Python SDK directly. The platform auto-injects `OPENAI_BASE_URL` and `OPENAI_API_KEY`, so `openai.OpenAI()` routes through the LLM Gateway with zero configuration.

```python
"""OpenAI SDK agent -- auto-routes through the platform LLM Gateway."""
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

    # Tools are called manually here; the platform mesh handles auth
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
    if name == "get_weather":
        url = context.tools.get("weather", "")
        resp = requests.post(f"{url}/weather/lookup", json={"city": args["city"]})
        return resp.json()
    return {"error": f"Unknown tool: {name}"}
```

**Deploy:**

=== "Console"
    Upload `agent.py`. The platform detects `import openai` (LLM usage) and `requests.post(...)` (tool call). Wire them to your registered model provider and weather tool.

=== "CLI"
    ```bash
    runagents deploy --files agent.py --name openai-agent
    ```

**What happens behind the scenes:**

1. `def handler(` detected → **Tier 2**
2. `import openai` and `import requests` detected → pip requirements auto-generated
3. At startup, the runtime calls `_inject_platform_env()` which sets `OPENAI_BASE_URL` to the LLM Gateway
4. `openai.OpenAI()` reads `OPENAI_BASE_URL` from the environment → all LLM calls go through the gateway
5. Tool calls via `requests.post()` are intercepted by the platform mesh → policy is checked and auth tokens are injected automatically

---

## Example 4: LangChain AgentExecutor

Use LangChain with an `AgentExecutor`. The runtime discovers the `executor` variable and wraps it automatically.

```python
"""LangChain agent with tools -- auto-discovered by the runtime."""
import os
import requests
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool


# The platform sets OPENAI_BASE_URL automatically -- ChatOpenAI reads it
llm = ChatOpenAI(
    model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    temperature=0,
)

WEATHER_URL = os.environ.get("TOOL_URL_WEATHER", "http://weather.agent-system.svc:8080")
CALCULATOR_URL = os.environ.get("TOOL_URL_CALCULATOR", "http://calculator.agent-system.svc:8080")


@tool
def get_weather(city: str) -> str:
    """Get current weather conditions for a city."""
    resp = requests.post(f"{WEATHER_URL}/weather/lookup", json={"city": city})
    data = resp.json()
    return f"{data.get('condition', 'Unknown')}, {data.get('temp_c', '?')}°C"


@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression. Supports: add, subtract, multiply, divide."""
    parts = expression.split()
    if len(parts) == 3:
        a, op, b = float(parts[0]), parts[1], float(parts[2])
        resp = requests.post(
            f"{CALCULATOR_URL}/calculate",
            json={"a": a, "b": b, "op": op},
        )
        return str(resp.json().get("result", "error"))
    return "Invalid expression format. Use: <number> <op> <number>"


prompt = ChatPromptTemplate.from_messages([
    ("system", os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant with access to weather and calculator tools.")),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, [get_weather, calculate], prompt)

# The runtime discovers this variable by name and wraps it
executor = AgentExecutor(agent=agent, tools=[get_weather, calculate], verbose=True)
```

**Deploy:**

=== "Console"
    Upload `agent.py` and `requirements.txt`. The platform detects LangChain imports → Tier 2 with custom image build.

=== "CLI"
    ```bash
    runagents deploy --files agent.py,requirements.txt --name langchain-agent
    ```

**requirements.txt:**
```
langchain>=0.3
langchain-openai>=0.3
requests
```

**What happens behind the scenes:**

1. `from langchain` and `AgentExecutor` detected → **Tier 2** with custom image build
2. The platform builds a container image from your code and pip requirements automatically
3. At startup, the runtime sets `OPENAI_BASE_URL` → `ChatOpenAI()` routes through the gateway
4. The runtime imports `agent.py`, finds `executor` (an `AgentExecutor`), and wraps it
5. Every `POST /invoke` calls `executor.invoke({"input": message})` and returns the output

---

## Example 5: LangGraph StateGraph

Use LangGraph for stateful, graph-based agent workflows. The runtime discovers the `graph` variable.

```python
"""LangGraph agent with a tool-calling node."""
import os
import json
import requests
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# --- State ---

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# --- LLM ---

llm = ChatOpenAI(
    model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    temperature=0,
)

CALCULATOR_URL = os.environ.get("TOOL_URL_CALCULATOR", "http://calculator.agent-system.svc:8080")

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform arithmetic: add, subtract, multiply, divide",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                    "op": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                },
                "required": ["a", "b", "op"],
            },
        },
    }
]

llm_with_tools = llm.bind_tools(tools_schema)


# --- Nodes ---

def call_model(state: AgentState) -> AgentState:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def call_tools(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        if tc["name"] == "calculate":
            resp = requests.post(f"{CALCULATOR_URL}/calculate", json=tc["args"])
            results.append(
                ToolMessage(content=json.dumps(resp.json()), tool_call_id=tc["id"])
            )
        else:
            results.append(
                ToolMessage(content=f"Unknown tool: {tc['name']}", tool_call_id=tc["id"])
            )
    return {"messages": results}


def should_call_tools(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"


# --- Graph ---

workflow = StateGraph(AgentState)
workflow.add_node("model", call_model)
workflow.add_node("tools", call_tools)

workflow.add_edge(START, "model")
workflow.add_conditional_edges("model", should_call_tools, {"tools": "tools", "end": END})
workflow.add_edge("tools", "model")

# The runtime discovers this variable by name and wraps it
graph = workflow.compile()
```

**Deploy:**

=== "Console"
    Upload `agent.py` and `requirements.txt`. The platform detects `StateGraph` → Tier 2 with custom image build.

=== "CLI"
    ```bash
    runagents deploy --files agent.py,requirements.txt --name langgraph-agent
    ```

**requirements.txt:**
```
langgraph>=0.3
langchain-openai>=0.3
requests
```

**What happens behind the scenes:**

1. `from langgraph` and `StateGraph` detected → **Tier 2** with custom image build
2. At startup, the runtime sets `OPENAI_BASE_URL` → `ChatOpenAI()` routes through the gateway
3. The runtime imports `agent.py`, finds `graph` (a `CompiledGraph`), and wraps it
4. Every `POST /invoke` calls `graph.invoke({"messages": [HumanMessage(content=message)]})` and returns the last message

---

## Choosing a Pattern

| Pattern | Best For | Tier | Custom Image? |
|---------|----------|------|---------------|
| Hello World | Quick demos, testing | 1 | No |
| `handler()` function | Full control, simple agents | 2 | Only if pip deps needed |
| OpenAI SDK | Direct SDK usage, custom tool calling | 2 | Yes |
| LangChain AgentExecutor | Chain-based agents with tools | 2 | Yes |
| LangGraph StateGraph | Stateful, graph-based workflows | 2 | Yes |

All patterns get the same platform features: identity propagation, policy enforcement, token injection, and mesh routing.

---

## What's Next

| Goal | Where to go |
|------|------------|
| Understand the runtime in detail | [Agent Runtime](../platform/agent-runtime.md) |
| Deploy your agent | [Deploying Agents](../platform/deploying-agents.md) |
| Register external tools | [Registering Tools](../platform/registering-tools.md) |
| Set up an LLM provider | [Model Providers](../platform/model-providers.md) |
