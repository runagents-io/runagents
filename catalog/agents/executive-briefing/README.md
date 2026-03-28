# Executive Briefing Agent

A LangGraph-based leadership productivity agent that assembles a concise executive briefing from meetings, project updates, stakeholder signals, and internal reference context.

## Why teams deploy this
Executive staff and business leads usually spend the first part of the day stitching together context from several systems before they can make decisions. This example shows how to automate that prep work without turning the result into an opaque black box.

Use it when you want a leadership-facing agent that can:
- prepare a daily or pre-meeting briefing in minutes instead of manual tab-hopping
- surface the few risks and decisions that actually need executive attention
- pull in supporting evidence from the systems your team already uses
- stay governed, auditable, and tool-routed through RunAgents

## What the agent will do for a user
When someone asks for a briefing, the agent starts with the request and any structured context already provided. It then decides what evidence it still needs, calls the right tools, and produces a tight brief that is useful to a real operator, not just a vague summary.

A typical result includes:
- the headline situation for the day or meeting
- the most important risks and blockers
- decisions that need executive input
- stakeholder signals worth paying attention to
- a recommended next step or question to resolve

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `calendar`, `project-tracker`, `knowledge-base`, `chat`
- Default policies: `leadership-readonly`, `internal-docs-readonly`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## What happens during a run
1. `ingest_request`
   Parses the incoming message. If the caller sends JSON, the graph can use inline `meetings`, `project_updates`, `reference_notes`, and `stakeholder_notes` as seed context.
2. `reasoning_agent`
   Uses the model as the decision-maker. It decides whether the current context is already enough or whether one or more tools should be called.
3. `tool_node`
   Executes LangChain-style tools through a `ToolNode`. Each tool wrapper is backed by `runagents.Agent().call_tool(...)`, so deploy-time tool selection still routes to the platform-registered tools.
4. `integrate_tool_outputs`
   Normalizes tool results into briefing context and evidence, then loops back to the reasoning agent.
5. `finalize_brief` (fallback)
   If the graph exhausts its tool budget, it still produces the best possible brief from the currently available context and clearly reflects any gaps.

## How models are called
- The graph creates a `ChatOpenAI` client with `LLM_MODEL`.
- RunAgents injects `OPENAI_BASE_URL` and `OPENAI_API_KEY`, so LangChain routes through the platform LLM gateway automatically.
- The model is used agentically in `reasoning_agent` to choose tool calls, ask for more evidence, and decide when it has enough signal to finalize.
- `finalize_brief` is only a safety fallback if the tool loop reaches its cap.

## How tools are called
- The graph defines standard LangChain tools with `@tool`.
- Those tool wrappers call `runagents.Agent().call_tool(...)` internally.
- That preserves the RunAgents runtime redirection model: the deployed agent uses the tools selected at deploy time via `TOOL_URL_*` wiring and any platform URL rewrites.
- In practice, that means policy checks, approvals, identity propagation, and audit stay inside RunAgents instead of being reimplemented in the example.

## Why the tools matter
- `calendar`: pulls the real meeting slate so the brief reflects the day's operating rhythm
- `project-tracker`: surfaces delivery risk, blocked work, and decisions that need escalation
- `knowledge-base`: grounds the brief in internal plans, runbooks, or reference docs
- `chat`: pulls stakeholder signals from systems like Slack or Teams so the brief reflects what people are actually worried about

## Example input
You can invoke the agent with plain text:

```text
Prepare today's executive briefing for the GTM leadership team.
```

Or with structured JSON to seed context directly:

```json
{
  "objective": "Prepare today's executive briefing for the GTM leadership team.",
  "meetings": [{"title": "Q2 launch review"}],
  "project_updates": [{"title": "Enterprise rollout", "status": "at_risk", "decision": "Approve vendor expansion"}],
  "stakeholder_notes": [{"signal": "Support volume increased in EMEA"}]
}
```

## What a strong deployment looks like
This example is strongest when you connect it to read-only systems that leadership already trusts:
- calendar data for the leadership or staff-cadence meetings
- project delivery data from a tracker such as Jira, Linear, or Asana
- internal docs or runbooks that capture current plans and decisions
- team messaging signals from Slack or Teams

That gives the model enough grounded evidence to produce a brief that is both fast and defensible.

## Deploy from CLI
If your RunAgents CLI is not configured yet:

```bash
runagents config set endpoint https://<your-runagents-endpoint>
runagents config set api-key <your-api-key>
runagents config set namespace <your-workspace-namespace>
```

Then deploy this example from the catalog directory:

```bash
cd catalog/agents/executive-briefing

runagents deploy \
  --name executive-briefing-agent \
  --file src/agent.py \
  --tool calendar \
  --tool project-tracker \
  --tool knowledge-base \
  --tool chat \
  --model openai/gpt-4.1
```

What this does:
- uploads `src/agent.py` as the agent source
- binds the four required platform tools
- sets the default reasoning model to `gpt-4.1`

## Deployment intent
Use this as a governed starting point for executive morning briefs, staff prep, and leadership decision digests. It is designed to show the stronger enterprise pattern: a true LangGraph reasoning loop where the model decides when to call tools, while every external tool call still goes through RunAgents-managed routing.
