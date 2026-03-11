# LangChain Enterprise Agent — RunAgents Identity & Policy Example

An enterprise HR assistant built with LangChain that demonstrates every
RunAgents security feature: identity propagation, policy enforcement,
just-in-time approvals, and OAuth2 credential injection.

```
HR Analyst → [RunAgents Ingress] → [LangChain Agent] → [HR Tools]
    JWT             validates              reasons          mesh enforces
                    extracts identity      tool calls       policies
                                                            injects creds
                                                            propagates identity
```

---

## What This Example Demonstrates

### 1. Identity Propagation
The user's identity (`X-End-User-ID`) flows from the JWT at the edge through
the agent to every tool call. Tools receive the verified end-user identity
without the agent touching any tokens.

```
Client JWT (email: analyst@corp.com)
  → Ingress validates, extracts email claim
    → Agent receives X-End-User-ID: analyst@corp.com
      → Tool receives X-End-User-ID: analyst@corp.com
```

Your LangChain code never handles tokens — the platform carries identity
end-to-end.

### 2. Three Policy Tiers

| Tool | Access Mode | PolicyBinding | Behaviour |
|------|-------------|--------------|-----------|
| `hr-knowledge-base` | Open | Auto-created by operator | Agent calls freely |
| `employee-directory` | Restricted | Must be created explicitly | Agent calls after binding |
| `compensation-api` | Restricted + `requireApproval` | Must be created, triggers JIT | First call pauses for admin approval |

### 3. JIT Approval Flow

```
Agent calls compensation-api
  → ext-authz checks PolicyBinding → requireApproval: true
    → governance creates AccessRequest (status: Pending)
      → run pauses (PAUSED_APPROVAL)
        → 403 APPROVAL_REQUIRED returned to agent
          → agent catches ApprovalRequired exception
            → returns: "Submitted for approval (action: act-xxx)"

Admin approves in console or CLI
  → AccessRequest status → Approved
    → ResumeWorker polls approved actions
      → calls /resume/act-xxx on agent pod
        → runtime restores checkpoint
          → re-executes compensation-api call (now allowed)
            → agent completes and responds
```

### 4. Durable Checkpointing — Resumes Even After Agent Failure

When approval is required, the runtime immediately saves the full
conversation state to **governance** (not to the agent pod):

```
approval triggered
  → runtime POSTs checkpoint to governance
    → checkpoint stored: messages + pending tool calls + tool definitions
      → agent pod can crash, restart, or be redeployed
        → resume still works — checkpoint is fetched from governance
          → runtime re-executes the pending calls and continues
```

**This means:**
- Pod crash between approval and resume → **still resumes correctly**
- Agent redeployed with a new version → **still resumes correctly**
- Node eviction, OOM kill, rolling restart → **still resumes correctly**

The checkpoint includes the complete conversation context — every LLM
message, every tool result, every pending call that was blocked. Your
LangChain code contributes nothing to this; it is entirely handled by
the platform runtime at the HTTP layer.

**Your LangChain code doesn't implement any of this.**
You only catch `ApprovalRequired` and return a user-facing message.

---

## Prerequisites

```bash
pip install runagents langchain langchain-openai requests
```

---

## Step 1: Credentials

```bash
runagents config set endpoint https://<your-id>.try.runagents.io
runagents config set api-key  ra_ws_YOUR_KEY_HERE
```

---

## Step 2: Register Tools

```bash
# Open tool — agent operator auto-creates PolicyBinding, agent can call immediately
runagents tools create \
  --name hr-knowledge-base \
  --base-url https://hr-api.your-company.com \
  --description "HR policy and procedures knowledge base. GET /articles/search" \
  --auth-type None \
  --access-mode Open

# Restricted tool — requires explicit PolicyBinding
runagents tools create \
  --name employee-directory \
  --base-url https://hr-api.your-company.com \
  --description "Employee directory. GET /employees/{id}" \
  --auth-type APIKey \
  --access-mode Restricted

# Restricted + approval — PolicyBinding must exist AND triggers JIT approval
runagents tools create \
  --name compensation-api \
  --base-url https://hr-api.your-company.com \
  --description "Compensation management. POST /compensation/{id}" \
  --auth-type OAuth2 \
  --access-mode Restricted
```

Or run `python deploy.py` — it registers all three and applies the policy YAML.

---

## Step 3: Apply Policy YAML

The `policy/` directory contains the Kubernetes YAML for policies and bindings.

### What the operator auto-creates (Open tools)

For `hr-knowledge-base` (Open), the agent operator automatically creates:

```yaml
# policy/auto-generated-open.yaml (for reference — you don't apply this)
apiVersion: platform.ai/v1alpha1
kind: Policy
metadata:
  name: hr-assistant-hr-knowledge-base
  namespace: agent-system
spec:
  rules:
    - resources: ["tool:hr-knowledge-base"]
      verbs: ["call"]
      effect: Allow
---
apiVersion: platform.ai/v1alpha1
kind: PolicyBinding
metadata:
  name: hr-assistant-hr-knowledge-base
  namespace: agent-system
spec:
  subjects:
    - kind: ServiceAccount
      name: hr-assistant
      namespace: default
  policyRef:
    name: hr-assistant-hr-knowledge-base
  requireApproval: false
```

**You don't apply this — the operator handles it.**

### What you must apply (Restricted tools)

Apply these yourself to grant access to the Restricted tools:

```bash
kubectl apply -f policy/employee-directory-binding.yaml
kubectl apply -f policy/compensation-binding.yaml
```

See `policy/` directory for the full YAML with explanations.

---

## Step 4: Deploy

```bash
python deploy.py
# or:
runagents deploy \
  --name hr-assistant \
  --files agent.py,tools.py,requirements.txt \
  --tool hr-knowledge-base \
  --tool employee-directory \
  --tool compensation-api \
  --model openai/gpt-4o-mini \
  --system-prompt "You are an HR assistant..."
```

---

## Step 5: Invoke

```bash
# This works immediately (Open tool, no approval needed)
curl -X POST https://<your-id>.try.runagents.io/api/agents/default/hr-assistant/invoke \
  -H "Authorization: Bearer ra_ws_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the company maternity leave policy?"}'

# This works if PolicyBinding exists for employee-directory
curl -X POST .../invoke \
  -d '{"message": "Look up employee ID EMP-042"}'

# This triggers JIT approval (requireApproval: true in PolicyBinding)
curl -X POST .../invoke \
  -d '{"message": "Update salary for EMP-042 to $95,000"}'
# Response: "Submitted for approval. Action ID: act-xxxxxxxx"
```

---

## Step 6: Handle the Approval

After a compensation update is requested:

```bash
# See the pending approval
runagents approvals list

# Output:
# ID:      act-xxxxxxxx
# Tool:    compensation-api
# Agent:   hr-assistant
# User:    analyst@corp.com   ← identity propagated end-to-end
# Action:  POST /compensation/EMP-042  {"salary": 95000}

# Approve it
runagents approvals approve act-xxxxxxxx
```

The ResumeWorker picks up the approved action within ~10 seconds,
calls `/resume/act-xxxxxxxx` on the agent pod, restores the checkpoint,
and completes the compensation update.

---

## Step 7: Monitor the Run

```bash
runagents runs list --agent hr-assistant

# Output:
# run-abc  PAUSED_APPROVAL  2026-03-11T10:00:00Z
# run-xyz  COMPLETED        2026-03-11T09:55:00Z

runagents runs get run-abc
# Events:
#   [01] invoke       {"message": "Update salary for EMP-042..."}
#   [02] tool_call    {"tool": "employee-directory", "input": {"id": "EMP-042"}}
#   [03] tool_result  {"employee": {"name": "Jane Doe", ...}}
#   [04] tool_call    {"tool": "compensation-api", "input": {...}}
#   [05] APPROVAL_REQUIRED  {"action_id": "act-xxxxxxxx", "tool": "compensation-api"}
```

---

## Local Development

```bash
# Terminal 1: mock tool server (shows identity headers being received)
python mock_tools/server.py

# Terminal 2: agent dev server
runagents dev

# Terminal 3: test (no JWT needed for local dev)
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -H "X-End-User-ID: developer@local" \
  -d '{"message": "What is the PTO policy?"}'
```

---

## Project Structure

```
langchain-enterprise/
├── README.md             # This file
├── agent.py              # LangChain ReAct agent + handler function
├── tools.py              # Tool definitions with identity + approval handling
├── runagents.yaml        # Agent config
├── requirements.txt      # Python dependencies
├── deploy.py             # One-shot deploy (tools + policy + agent)
├── policy/
│   ├── README.md         # Policy model explanation
│   ├── employee-directory-binding.yaml   # Apply to grant access
│   └── compensation-binding.yaml         # Apply — triggers JIT on first call
└── mock_tools/
    └── server.py         # Local mock showing identity header flow
```
