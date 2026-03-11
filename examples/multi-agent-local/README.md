# Multi-Agent Customer Support

A three-agent LangChain system that runs locally and deploys to RunAgents
without any code changes.

```
User message
    ↓
Coordinator         classifies and routes
    ├── KnowledgeAgent   searches FAQ / knowledge base
    └── AccountAgent     handles account lookups and plan changes
```

---

## Run Locally

```bash
pip install langchain langchain-openai requests
export OPENAI_API_KEY=sk-...

# Terminal 1 — start the mock API server
python mock_server.py

# Terminal 2 — run the agent
python agent.py "What is your return policy?"
python agent.py "Look up account CUST-001"
python agent.py "Upgrade CUST-002 to the pro plan"
python agent.py "Create a billing ticket for CUST-003"
```

---

## Deploy to RunAgents

```bash
pip install runagents

runagents config set endpoint https://YOUR_WORKSPACE.try.runagents.io
runagents config set api-key  ra_ws_YOUR_KEY

# Register tools — point base-url at your real APIs
runagents tools create --name faq-service     --base-url https://api.your-company.com --auth-type None
runagents tools create --name account-service --base-url https://api.your-company.com --auth-type APIKey
runagents tools create --name ticket-service  --base-url https://api.your-company.com --auth-type None

# Deploy — same agent.py and tools.py, no changes
runagents deploy \
  --name support-agent \
  --files agent.py,tools.py,requirements.txt \
  --tool faq-service \
  --tool account-service \
  --tool ticket-service \
  --model openai/gpt-4o-mini
```

**No changes to agent.py or tools.py.** The platform discovers the
`chain` variable in `agent.py` and calls `chain.invoke({"input": message})`
on each request.

---

## How the Platform Discovers Your Agent

The RunAgents runtime looks for well-known variable names in your entry
point module. In this example, `agent.py` exposes:

```python
chain = RunnableLambda(lambda x: coordinator(x["input"]))
```

The runtime finds `chain`, sees it has an `.invoke()` method, and calls
it for every request. No handler function, no platform imports.

The same discovery works for `agent`, `executor`, `graph` (LangGraph),
and `crew` (CrewAI) — whatever you already expose in your code.

---

## What the Platform Adds

Once deployed, the platform wraps your existing code with:

**Identity** — every request carries a JWT from your identity provider.
The platform validates it at the ingress, extracts the user's identity
(e.g. email), and forwards it as `X-End-User-ID` to every tool call.
Your `account-service` and `ticket-service` receive `who` made the
request without any code in this repo touching tokens.

**Policy** — tool access is controlled by PolicyBindings on the cluster.
`faq-service` and `ticket-service` are Open (auto-bound). `account-service`
is Restricted — you apply a PolicyBinding YAML to grant access, and can
set `requireApproval: true` to require human sign-off per call.

**Credentials** — `account-service` uses `--auth-type APIKey`. The platform
stores the key in a Kubernetes Secret and injects `Authorization: Bearer`
on every outbound call via the Istio mesh. Your `tools.py` never sees it.

**Durable resume** — if a tool requires approval, the platform checkpoints
the full conversation to governance and resumes automatically after approval,
even if the agent pod restarts in between.

---

## Files

```
multi-agent-local/
├── agent.py        # Pure LangChain — coordinator + two specialist agents
├── tools.py        # LangChain tools reading TOOL_URL_* env vars
├── mock_server.py  # Local mock API (FAQ, accounts, tickets)
├── runagents.yaml  # Platform config
├── requirements.txt
└── .env.example
```
