# Multi-Agent Customer Support — Local → RunAgents

A three-agent customer support system built with LangChain.
Runs locally out of the box. Deploy to RunAgents to add identity,
policy enforcement, and credential injection — **zero code changes**.

```
User message
    ↓
Coordinator         classifies and routes
    ├── KnowledgeAgent   searches FAQ / knowledge base
    └── AccountAgent     handles account lookups and changes
```

---

## Run Locally

```bash
pip install langchain langchain-openai requests
export OPENAI_API_KEY=sk-...

# Terminal 1 — mock API server
python mock_server.py

# Terminal 2 — ask the agent
python agent.py "What is your return policy?"
python agent.py "Look up account CUST-001"
python agent.py "Upgrade CUST-002 to the pro plan"
python agent.py "Create a billing ticket for CUST-003, they were double charged"
```

No platform, no config, no deployment needed.

---

## Deploy to RunAgents

```bash
pip install runagents

runagents config set endpoint https://YOUR_WORKSPACE.try.runagents.io
runagents config set api-key  ra_ws_YOUR_KEY

# Register tools (point base-url at your real APIs)
runagents tools create --name faq-service     --base-url https://api.your-company.com --auth-type None
runagents tools create --name account-service --base-url https://api.your-company.com --auth-type APIKey --access-mode Restricted
runagents tools create --name ticket-service  --base-url https://api.your-company.com --auth-type None

# Deploy
runagents deploy \
  --name support-agent \
  --files agent.py,tools.py,requirements.txt \
  --tool faq-service \
  --tool account-service \
  --tool ticket-service \
  --model openai/gpt-4o-mini
```

The agent code is identical between local and deployed.

---

## What the Platform Adds (Without Code Changes)

### Identity
Every request carries a JWT from your identity provider. The platform
validates it at the ingress and extracts the user's identity (e.g. email)
into an `X-End-User-ID` header. The runtime passes it to `handler()` as
`request["user_id"]`. Every tool call then carries the user's verified
identity — `account-service` and `ticket-service` know exactly who is
making each request.

```
Client JWT (sub: user@corp.com)
  → ingress validates + extracts
    → X-End-User-ID: user@corp.com
      → handler() receives request["user_id"]
        → tools.py sets X-End-User-ID on every outbound call
          → account-service logs: changed_by = user@corp.com
```

### Policy
Tool access is controlled by PolicyBindings on the cluster, not in code.

| Tool | Access | Behaviour |
|------|--------|-----------|
| `faq-service` | Open | Agent operator creates PolicyBinding automatically — works on first deploy |
| `account-service` | Restricted | Apply `kubectl apply -f` a PolicyBinding YAML, or use the console |
| `ticket-service` | Open | Same as faq-service — works automatically |

To require human approval before `account-service` allows plan changes,
set `requireApproval: true` in the PolicyBinding. The run will pause and
resume automatically after an admin approves — your agent code is unchanged.

### Credentials
`account-service` uses `--auth-type APIKey`. The platform stores the key
in a Kubernetes Secret and injects it as `Authorization: Bearer <key>` on
every outbound call via the Istio mesh. Your tool code never sees the key.

### Durable Resume
If a tool requires approval and the agent pod restarts before the approval
is granted, the run still resumes correctly. The conversation checkpoint is
stored in governance — not in the pod — so resume works regardless of what
happens to the agent process.

---

## Structure

```
multi-agent-local/
├── agent.py        # Coordinator + KnowledgeAgent + AccountAgent
├── tools.py        # HTTP tool wrappers (same code local and deployed)
├── mock_server.py  # Local mock API for all three tools
├── runagents.yaml  # Platform config (tools, model, system prompt)
├── requirements.txt
└── .env.example
```

The coordinator and specialist agents are all in `agent.py` — easy to read
as a whole. `tools.py` is the only file that touches external APIs.
