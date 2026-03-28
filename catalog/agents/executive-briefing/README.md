# Executive Briefing Agent

A LangGraph-based leadership productivity agent that assembles a concise daily briefing from meetings, project updates, stakeholder signals, and internal reference context.

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `calendar`, `project-tracker`, `knowledge-base`, `chat`
- Default policies: `leadership-readonly`, `internal-docs-readonly`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## Graph flow
1. `ingest_request`
   Parses the incoming message. If the caller sends JSON, the graph can use inline `meetings`, `project_updates`, `reference_notes`, and `stakeholder_notes` as seed context.
2. `reasoning_agent`
   Uses the model as the decision-maker. It decides whether the current context is enough or whether one or more tools should be called.
3. `tool_node`
   Executes LangChain-style tools through a `ToolNode`. Each tool wrapper is backed by `runagents.Agent().call_tool(...)`, so deploy-time tool selection still routes to the platform-registered tools.
4. `integrate_tool_outputs`
   Normalizes tool results into briefing context and evidence, then loops back to the reasoning agent.
5. `finalize_brief` (fallback)
   If the graph exhausts its tool budget, it produces the best possible final brief from the currently available context.

## How models are called
- The graph creates a `ChatOpenAI` client with `LLM_MODEL`.
- RunAgents injects `OPENAI_BASE_URL` and `OPENAI_API_KEY`, so LangChain routes through the platform LLM gateway automatically.
- The model is used agentically in `reasoning_agent` to choose tool calls.
- The model can return the final executive brief directly once it decides it has enough context.
- `finalize_brief` is only a safety fallback if the tool loop reaches its cap.

## How tools are called
- The graph defines standard LangChain tools with `@tool`.
- Those tool wrappers call `runagents.Agent().call_tool(...)` internally.
- That preserves the RunAgents runtime redirection model: the deployed agent uses the tools selected at deploy time via `TOOL_URL_*` wiring and any platform URL rewrites.
- If a connector is unavailable, the graph degrades gracefully and still produces a useful briefing with explicit gaps.

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
Use this as a governed starting point for executive morning briefs, staff prep, and leadership decision digests. The example is designed to show the stronger enterprise pattern: a true LangGraph reasoning loop where the model decides when to call tools, while every external tool call still goes through RunAgents-managed routing for policy, approvals, identity propagation, and audit.
