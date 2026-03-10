# Agent Runtime

The RunAgents agent runtime is the execution layer that runs your AI agent inside the platform. It handles LLM communication, tool calling, and mesh integration so your code can focus on agent logic.

---

## Two-Tier Model

RunAgents supports two deployment tiers, chosen automatically based on your code:

### Tier 1: Platform Runtime (No Custom Code)

Your agent runs on the pre-built RunAgents runtime image. The runtime provides:

- A built-in **tool-calling loop** that uses the LLM to decide which tools to call
- Automatic **system prompt** injection
- **OpenAI-format function calling** with tool definitions generated from your Tool CRDs

**When is Tier 1 used?** When your source code has no custom handler function or framework imports. For example, a simple script that calls `requests.post()` against known URLs. The platform analyzes your code at deploy time and routes it to Tier 1 if no custom code patterns are detected.

**What the runtime does:**

1. Sends your system prompt + user message + tool definitions to the LLM
2. If the LLM returns tool calls, executes them via HTTP (policy-checked and authenticated by the platform)
3. Feeds tool results back to the LLM
4. Repeats until the LLM produces a final text response (up to `MAX_TOOL_ITERATIONS`)

### Tier 2: Custom Code

Your agent includes a handler function or uses a framework (LangChain, LangGraph, CrewAI). The platform builds a container image with your code and dependencies, then runs it with all platform env vars injected.

**When is Tier 2 used?** When your source code contains any of these patterns:

- `def handler(` -- a handler function
- `AgentExecutor`, `create_openai_tools_agent` -- LangChain
- `StateGraph`, `CompiledGraph` -- LangGraph
- `@CrewBase` -- CrewAI
- `from langchain`, `from langgraph`, `from crewai`, `from autogen` -- framework imports

Tier 2 agents still get all platform env vars and mesh routing. The difference is that **your code controls the execution flow** instead of the built-in tool loop.

---

## Platform Environment Injection

At startup, the runtime automatically sets SDK-compatible environment variables so that popular AI SDKs route through the platform's LLM Gateway without any configuration in your code.

The following are set **only if not already present** (your explicit config always wins):

| Variable | Value | Used By |
|----------|-------|---------|
| `OPENAI_BASE_URL` | LLM Gateway base URL (e.g., `http://llm-gateway.agent-system.svc:8080/v1`) | OpenAI Python SDK, LangChain |
| `OPENAI_API_BASE` | Same as above | Older OpenAI SDK versions |
| `OPENAI_API_KEY` | `platform-managed` | OpenAI Python SDK (required but unused -- auth is handled by the mesh) |
| `ANTHROPIC_BASE_URL` | LLM Gateway base URL | Anthropic Python SDK |
| `ANTHROPIC_API_KEY` | `platform-managed` | Anthropic Python SDK |

This means that code like `openai.OpenAI()` or `ChatOpenAI()` will automatically route through the LLM Gateway with zero configuration.

---

## User Code Discovery

When `USER_ENTRY_POINT` is set (Tier 2 agents), the runtime imports the specified Python module and searches for a callable using this priority:

### Priority 1: `handler()` Function

```python
def handler(request, context):
    message = request["message"]
    # Your logic here
    return {"response": "..."}
```

The simplest pattern. The runtime calls your `handler()` with a request dict and an optional `RunContext`.

### Priority 2: Framework Objects

The runtime looks for module-level variables named `agent`, `chain`, `executor`, `graph`, or `crew`:

| Variable Name | Expected Type | How It's Called |
|---------------|---------------|-----------------|
| `agent` | Any with `.invoke()` | `agent.invoke({"input": message})` |
| `chain` | LangChain Chain | `chain.invoke({"input": message})` |
| `executor` | LangChain AgentExecutor | `executor.invoke({"input": message})` |
| `graph` | LangGraph CompiledGraph | `graph.invoke({"messages": [HumanMessage(content=message)]})` |
| `crew` | CrewAI Crew | `crew.kickoff(message)` |

### Priority 3: `main()` Function

```python
def main(request):
    return {"response": "..."}
```

Fallback for simple scripts.

---

## RunContext API

When your handler accepts two arguments, the second is a `RunContext` object:

```python
def handler(request, context):
    # context.tools    -- dict of {tool-name: url}
    # context.llm_url  -- LLM Gateway URL
    # context.model    -- model name (e.g., "gpt-4o-mini")
    # context.system_prompt -- configured system prompt
    # context.session   -- dict for conversation state (in-memory)
    pass
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `tools` | `dict[str, str]` | Map of tool name to base URL. Built from `TOOL_URL_*` env vars. |
| `llm_url` | `str` | Full LLM Gateway URL for chat completions. |
| `model` | `str` | Model name from `LLM_MODEL` env var. |
| `system_prompt` | `str` | System prompt from `SYSTEM_PROMPT` env var. |
| `session` | `dict` | In-memory conversation state. Contains `history` from the request. |

### Example

```python
def handler(request, context):
    import urllib.request, json

    # Call a tool using the platform-provided URL
    tool_url = context.tools["calculator"]
    data = json.dumps({"a": 5, "b": 3, "op": "add"}).encode()
    req = urllib.request.Request(
        f"{tool_url}/calculate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    return {"response": f"5 + 3 = {result['result']}"}
```

---

## Injected Environment Variables

The operator generates a ConfigMap for each agent with these environment variables:

### Core Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `SYSTEM_PROMPT` | Agent CRD `.spec.systemPrompt` | System prompt for the LLM |
| `LLM_GATEWAY_URL` | Resolved from ModelProvider | Full URL to LLM Gateway chat completions endpoint |
| `LLM_MODEL` | Agent CRD `.spec.llmConfig.model` | Primary model name (e.g., `gpt-4o-mini`) |
| `LLM_PROVIDER` | Agent CRD `.spec.llmConfig.provider` | Provider name (e.g., `openai`) |
| `LLM_PROVIDER_NAME` | Resolved ModelProvider CRD name | Name of the matched ModelProvider resource |
| `AGENT_NAME` | Agent CRD `.metadata.name` | Agent name (used in logs) |
| `USER_ENTRY_POINT` | Agent CRD `.spec.entryPoint` | Python module to import for Tier 2 agents |

### Tool Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `TOOL_URL_{NAME}` | Tool CRD `.spec.connection.baseUrl` | Base URL for each required tool. Name is uppercased with hyphens replaced by underscores. |
| `TOOL_NAMES` | Computed from required tools | Comma-separated list of tool names |
| `TOOL_DEFINITIONS_JSON` | Generated from Tool CRD capabilities | OpenAI-format tool definitions array (JSON string) |
| `TOOL_ROUTES_JSON` | Generated from Tool CRD capabilities | Function name to HTTP route mapping (JSON string) |

### Multi-Model Variables

When multiple LLM configs are specified with different roles:

| Variable | Description |
|----------|-------------|
| `LLM_MODEL_EMBEDDING` | Model name for the embedding role |
| `LLM_PROVIDER_EMBEDDING` | Provider for the embedding role |
| `LLM_MODEL_CLASSIFY` | Model name for the classify role |
| `LLM_PROVIDER_CLASSIFY` | Provider for the classify role |
| `LLM_MODEL_RERANKING` | Model name for the reranking role |
| `LLM_PROVIDER_RERANKING` | Provider for the reranking role |

### Runtime Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TOOL_ITERATIONS` | `10` | Maximum tool-calling loop iterations before stopping |
| `PORT` | `8080` | HTTP server port |

---

## Outbound Call Flow

When your agent calls a tool, the request is intercepted by the platform's zero-trust network layer:

```
Agent  →  Platform Network Layer  →  Tool
                    │
                    ├─ Identify target tool
                    ├─ Verify agent identity
                    ├─ Check access policy
                    ├─ Enforce capability restrictions (method + path)
                    └─ Inject authentication token
```

1. Your agent makes a plain HTTP call to the tool's base URL
2. The platform intercepts the outbound request transparently
3. Access policy is checked and an auth token is optionally injected
4. If the tool requires approval and no policy exists, the agent receives a 403 with `APPROVAL_REQUIRED`
5. If allowed, the request reaches the tool with proper authentication

Your code never handles authentication tokens directly. The mesh injects them transparently.

---

## HTTP Endpoints

The runtime exposes these endpoints on the agent pod:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` or `/healthz` | Health check. Returns agent name, model, tool count, user code status. |
| `GET` | `/readyz` | Readiness probe. Pings LLM Gateway `/healthz`. Returns 503 if unreachable. |
| `POST` | `/invoke` | Send a message and get a response (synchronous). |
| `POST` | `/invoke/stream` | Send a message and get SSE events (streaming). |

### POST /invoke

Request:
```json
{
  "message": "What is 2 + 2?",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello!"}
  ]
}
```

Response:
```json
{
  "response": "2 + 2 = 4",
  "model": "gpt-4o-mini",
  "usage": {"prompt_tokens": 150, "completion_tokens": 12, "total_tokens": 162},
  "tool_calls_made": [
    {"function": "calculator__add", "method": "POST", "url": "http://calculator.agent-system.svc:8080/calculate"}
  ],
  "duration_ms": 1234,
  "request_id": "abc-123"
}
```

### POST /invoke/stream

Same request format. Returns Server-Sent Events:

```
data: {"type":"tool_call","tool":"calculator__add","arguments":"{\"a\":2,\"b\":2,\"op\":\"add\"}"}

data: {"type":"tool_result","tool":"calculator__add","result":"{\"result\":4}"}

data: {"type":"content","delta":"2 + 2 = 4"}

data: {"type":"done","model":"gpt-4o-mini","tool_calls_made":[...]}

data: [DONE]
```

---

## What's Next

| Goal | Where to go |
|------|------------|
| See complete code examples | [Writing Agents](../getting-started/writing-agents.md) |
| Deploy an agent | [Deploying Agents](deploying-agents.md) |
| Register tools for your agent | [Registering Tools](registering-tools.md) |
| Configure an LLM provider | [Model Providers](model-providers.md) |
