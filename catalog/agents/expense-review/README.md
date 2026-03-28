# Expense Review Agent

A LangGraph-based finance operations agent that assembles a review packet from expense submission details and ERP policy context.

## Why teams deploy this
Finance teams often spend time gathering evidence before they can even begin to review a submission. This example shows how to automate the evidence collection and first-pass reasoning while keeping the workflow policy-aware and approval-friendly.

Use it when you want an agent that can:
- prepare a clean packet for finance reviewers before they open the case
- cross-reference an expense against policy and ERP context
- highlight exceptions, missing receipts, or suspicious line items
- reduce manual triage while keeping sensitive decisions governed

## What the agent will do for a user
A finance reviewer, manager, or audit analyst can ask the agent to review an expense packet. The agent will inspect the current submission, gather missing policy context, and return a finance-ready review summary.

A typical result includes:
- the key facts of the submission
- which rules or thresholds appear relevant
- possible exceptions or anomalies
- follow-up evidence that is still missing
- the next recommendation for approve, hold, or escalate

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `erp`, `expense-system`
- Default policies: `approval-required`, `finance-readonly`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## What happens during a run
1. `ingest_request`
   Parses plain text or structured JSON and seeds expense submission details if they were already supplied.
2. `reasoning_agent`
   Uses the model to decide whether it needs more evidence from ERP policy context or the expense submission system.
3. `tool_node`
   Executes standard LangChain `@tool` wrappers backed by `runagents.Agent().call_tool(...)`.
4. `integrate_tool_outputs`
   Normalizes the evidence into a finance review packet and loops back into the reasoning step.
5. `finalize_review`
   Safety fallback if the tool budget is exhausted.

## How models are called
- The example uses `ChatOpenAI` with `LLM_MODEL`.
- RunAgents injects the OpenAI-compatible env vars, so the graph routes through the platform LLM gateway automatically.
- The model decides when more evidence is needed and when the review packet is complete.

## How tools are called
- The example uses standard LangChain `@tool` wrappers.
- Each wrapper calls `runagents.Agent().call_tool(...)`, so the deployed agent still uses the tools selected at deploy time.
- That preserves approval routing, policy checks, audit, and identity propagation for every tool call.

## Why the tools matter
- `erp`: supplies finance policy context, cost-center rules, and system-of-record data
- `expense-system`: provides the current report, receipts, line items, and traveler metadata

## Example input
Plain text:

```text
Review the latest conference travel reimbursement packet.
```

Structured JSON:

```json
{
  "objective": "Review the latest conference travel reimbursement packet.",
  "expense_report": [{"merchant": "Hilton", "amount": "1290 USD", "reason": "Conference stay"}]
}
```

## What a strong deployment looks like
This example is strongest when it is connected to:
- a system of record for expense submissions and receipts
- an ERP or finance policy source that exposes reimbursement rules, categories, and approval thresholds

With both in place, the agent can do useful triage before a human approver needs to step in.

## Deploy from CLI
If your RunAgents CLI is not configured yet:

```bash
runagents config set endpoint https://<your-runagents-endpoint>
runagents config set api-key <your-api-key>
runagents config set namespace <your-workspace-namespace>
```

Then deploy this example:

```bash
cd catalog/agents/expense-review

runagents deploy \
  --name expense-review-agent \
  --file src/agent.py \
  --tool erp \
  --tool expense-system \
  --model openai/gpt-4.1
```

## Deployment intent
Use this as a governed starting point for finance triage, policy exception review, and approval packet preparation.
