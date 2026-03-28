# Customer Escalation Agent

A LangGraph-based customer operations agent that builds a shared escalation brief from CRM context, incident posture, runbook evidence, and cross-functional signals.

## Why teams deploy this
High-priority customer issues usually fail because context is fragmented: account history is in the CRM, technical posture is in ticketing, tribal knowledge is in docs, and urgency is in Slack or Teams. This example shows how to unify that context fast enough for a real escalation.

Use it when you want an agent that can:
- assemble a customer-facing escalation brief before an exec or account call
- surface what matters across support, engineering, and customer success
- identify the missing evidence before people make commitments
- reduce the amount of manual coordination needed to get everyone aligned

## What the agent will do for a user
A support lead, account owner, or response manager can ask for an escalation brief. The agent will inspect the request, pull the most relevant context from the connected systems, and return a shared operating picture.

A typical result includes:
- customer and account context
- current incident state and known impact
- evidence from tickets, KB, and stakeholder chatter
- risks for renewal, trust, or executive visibility
- the next best action for the response team

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `crm`, `ticketing`, `knowledge-base`, `chat`
- Default policies: `support-readonly`, `customer-data-guardrails`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## What happens during a run
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

## Why the tools matter
- `crm`: provides the account relationship, contract context, and customer importance
- `ticketing`: gives the live incident trail and operational status
- `knowledge-base`: grounds the brief in runbooks, previous incidents, and internal reference material
- `chat`: captures urgency, stakeholder pressure, and coordination signals from messaging systems

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

## What a strong deployment looks like
This example works best when it can see both business and technical context:
- account and renewal information from CRM
- incident tickets or case data from support systems
- known procedures from docs or KB systems
- active coordination context from Slack or Teams

That lets the agent produce a brief that is useful for both internal responders and customer-facing teams.

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
