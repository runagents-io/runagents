# LangChain Enterprise Agent (Policy-Driven Approval)

This example demonstrates identity propagation, policy enforcement, and JIT approvals for an HR assistant.

---

## What It Demonstrates

- Agent calls to multiple HR tools
- Policy-based allow and `approval_required` decisions
- Run pause/resume on approval
- End-user identity propagation (`X-End-User-ID`) to downstream tools

---

## Architecture

```
HR Analyst -> RunAgents -> hr-assistant (LangChain) -> HR tools
                        \-> policy evaluation on every tool call
```

---

## Prerequisites

```bash
pip install runagents langchain langchain-openai requests
runagents config set endpoint https://<your-workspace>.try.runagents.io
runagents config set api-key ra_ws_<your_key>
runagents config set namespace default
```

---

## 1) Register Tools

Use the console or API to register these tools:

- `hr-knowledge-base` -> `https://knowledge.hr-api.your-company.com`
- `employee-directory` -> `https://directory.hr-api.your-company.com`
- `compensation-api` -> `https://compensation.hr-api.your-company.com`

The tool URLs should align with policy resource patterns in `policy/*.yaml`.

---

## 2) Deploy Agent

```bash
python deploy.py
```

Or deploy directly:

```bash
runagents deploy \
  --name hr-assistant \
  --file agent.py \
  --file tools.py \
  --file requirements.txt \
  --tool hr-knowledge-base \
  --tool employee-directory \
  --tool compensation-api \
  --model openai/gpt-4o-mini
```

---

## 3) Apply Policies

```bash
kubectl apply -f policy/employee-directory-binding.yaml
kubectl apply -f policy/compensation-binding.yaml
```

These policies bind access to ServiceAccount `hr-assistant`.

---

## 4) Invoke

```bash
curl -X POST https://<workspace>.try.runagents.io/api/agents/default/hr-assistant/invoke \
  -H "Authorization: Bearer ra_ws_<your_key>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Look up employee EMP-042"}'
```

For compensation writes, policy should return `APPROVAL_REQUIRED`.

---

## 5) Approve

```bash
runagents approvals list
runagents approvals approve <request-id>
```

After approval, blocked run actions are resumed automatically.

---

## Key Policy Behavior

- `employee-directory`: `allow` rule for read operations.
- `compensation-api`: `approval_required` rule for write operations.
- Precedence: `deny` > `approval_required` > `allow` > default deny.

---

## Files

- `agent.py` — LangChain orchestration
- `tools.py` — Tool wrappers
- `deploy.py` — Example deploy helper
- `policy/employee-directory-binding.yaml`
- `policy/compensation-binding.yaml`

