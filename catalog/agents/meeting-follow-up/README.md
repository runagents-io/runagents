# Meeting Follow-Up Agent

A LangGraph-based productivity agent that turns meeting context into a clean recap, grounded decisions, and actionable next steps.

## Why teams deploy this
A lot of meetings create work, but very few teams capture that work consistently. This example is meant for teams that want the value of strong follow-through without depending on someone to manually clean up notes after every session.

Use it when you want an agent that can:
- turn a meeting into a crisp summary people will actually read
- extract decisions, owners, and open questions from messy notes
- pull missing context from calendars, docs, trackers, and chat
- produce a follow-up that is ready to send or copy into your workflow system

## What the agent will do for a user
A user can ask for a follow-up after a sync, planning meeting, incident review, or customer conversation. The agent will look at what was provided, decide what context it still needs, gather that context, and then return a structured follow-up.

A typical result includes:
- what happened in the meeting
- the decisions that were made
- actions and owners
- unresolved questions or dependencies
- suggested next communication or handoff

## What it includes
- Suggested model: `gpt-4.1-mini`
- Required tools: `calendar`, `docs`, `project-tracker`, `chat`
- Default policies: `meeting-readonly`, `task-write-approval`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## What happens during a run
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
- The model decides whether more retrieval is needed and when the meeting recap is complete enough to send back.

## How tools are called
- The example uses standard LangChain `@tool` wrappers.
- Each wrapper calls `runagents.Agent().call_tool(...)` so deploy-time tool selection still controls the actual tool endpoints.
- That preserves policy, approvals, audit, and identity propagation on every external tool call.

## Why the tools matter
- `calendar`: resolves which meeting the user is referring to and supplies meeting metadata
- `docs`: pulls notes, agendas, or linked documents
- `project-tracker`: grounds action items in the real delivery system
- `chat`: pulls follow-up signals from Slack or Teams when decisions or owners were discussed there

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

## What a strong deployment looks like
This example becomes especially useful when it sits on top of the systems your team already relies on after meetings:
- a calendar source to anchor the meeting
- docs or notes for agenda and recap content
- a tracker for delivery tasks and ownership
- messaging context for open questions and social alignment

That combination lets the agent do more than summarize. It can actually help drive follow-through.

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
