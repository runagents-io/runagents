# Customer Escalation Agent

A LangGraph-based customer operations agent that builds a shared escalation brief from CRM context, incident posture, runbook evidence, and cross-functional signals.

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `crm`, `ticketing`, `knowledge-base`, `chat`
- Default policies: `support-readonly`, `customer-data-guardrails`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## Graph flow
1. `ingest_request`
   Parses either plain text or structured JSON and seeds customer, incident, and stakeholder context when it is already available.
2. `reasoning_agent`
   Uses the model to decide whether the existing evidence is enough or whether more tool calls are needed.
3. `tool_node`
   Executes standard LangChain `@tool` wrappers backed by `runagents.Agent().call_tool(...)`.
4. `integrate_tool_outputs`
   Normalizes CRM, ticketing, KB, and messaging results into escalation context and loops back to the reasoning agent.
5. `finalize_brief`
   Safety fallback if the workflow hits its tool budget.

## How models are called
- The example uses `ChatOpenAI` with `LLM_MODEL`.
- RunAgents injects the OpenAI-compatible env vars, so LangGraph routes through the platform LLM gateway automatically.
- The model decides whether to gather more context or finalize the escalation brief.

## How tools are called
- The example defines standard LangChain tools with `@tool`.
- Each wrapper calls `runagents.Agent().call_tool(...)` internally.
- That keeps the example idiomatic to LangGraph while preserving RunAgents tool routing, policy checks, approvals, and audit.

## Example input
Plain text:

```text
Prepare a customer escalation brief for the Acme renewal outage.
```

Structured JSON:

```json
{
  "objective": "Prepare a customer escalation brief for the Acme renewal outage.",
  "account": [{"name": "Acme", "impact": "Renewal risk"}],
  "incident": [{"title": "Billing sync outage", "severity": "sev-1"}],
  "stakeholder_signals": [{"signal": "CS leadership wants an ETA before customer call"}]
}
```

## Deploy from CLI
If your RunAgents CLI is not configured yet:

```bash
runagents config set endpoint https://<your-runagents-endpoint>
runagents config set api-key <your-api-key>
runagents config set namespace <your-workspace-namespace>
```

Then deploy this example:

```bash
cd catalog/agents/customer-escalation

runagents deploy \
  --name customer-escalation-agent \
  --file src/agent.py \
  --tool crm \
  --tool ticketing \
  --tool knowledge-base \
  --tool chat \
  --model openai/gpt-4.1
```

## Deployment intent
Use this as a governed starting point for high-priority customer escalations, executive visibility briefs, and cross-functional response coordination.
