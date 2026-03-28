# Meeting Follow-Up Agent

A LangGraph-based productivity agent that turns meeting context into a clean recap, grounded decisions, and actionable next steps.

## What it includes
- Suggested model: `gpt-4.1-mini`
- Required tools: `calendar`, `docs`, `project-tracker`, `chat`
- Default policies: `meeting-readonly`, `task-write-approval`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## Graph flow
1. `ingest_request`
   Parses plain text or structured JSON and seeds meeting notes, action items, or stakeholder context if the caller already has them.
2. `reasoning_agent`
   Uses the model to decide whether the current context is enough or whether it should fetch more meeting metadata, notes, delivery context, or messaging signals.
3. `tool_node`
   Executes standard LangChain `@tool` wrappers backed by `runagents.Agent().call_tool(...)`.
4. `integrate_tool_outputs`
   Normalizes the retrieved context and loops back into the reasoning step.
5. `finalize_followup`
   Safety fallback if the tool budget is exhausted.

## How models are called
- The example uses `ChatOpenAI` with `LLM_MODEL`.
- RunAgents injects the OpenAI-compatible env vars, so the graph routes through the platform LLM gateway automatically.
- The model decides when more retrieval is needed and when the recap is ready.

## How tools are called
- The example uses standard LangChain `@tool` wrappers.
- Each wrapper calls `runagents.Agent().call_tool(...)` so deploy-time tool selection still controls the actual tool endpoints.
- That preserves policy, approvals, audit, and identity propagation on every external tool call.

## Example input
Plain text:

```text
Prepare a follow-up for the weekly product sync.
```

Structured JSON:

```json
{
  "objective": "Prepare a follow-up for the weekly product sync.",
  "meeting": [{"title": "Weekly product sync", "owner": "Alicia"}],
  "notes": [{"summary": "Launch date held, onboarding docs still behind"}],
  "action_items": [{"task": "Update onboarding checklist", "owner": "Growth ops"}]
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
cd catalog/agents/meeting-follow-up

runagents deploy \
  --name meeting-follow-up-agent \
  --file src/agent.py \
  --tool calendar \
  --tool docs \
  --tool project-tracker \
  --tool chat \
  --model openai/gpt-4.1-mini
```

## Deployment intent
Use this as a governed starting point for meeting recap automation, action-item capture, and team follow-through workflows.
