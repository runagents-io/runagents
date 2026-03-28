# Executive Briefing Agent

A LangGraph-based leadership productivity agent that assembles a concise daily briefing from meetings, project updates, stakeholder signals, and internal reference context.

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `calendar`, `project-tracker`, `knowledge-base`, `chat`
- Default policies: `leadership-readonly`, `internal-docs-readonly`
- Authoring pattern: `LangGraph + ToolNode`

## Graph flow
1. `ingest_request`
   Parses the incoming message. If the caller sends JSON, the graph can use inline `meetings`, `project_updates`, `reference_notes`, and `stakeholder_notes` as seed context.
2. `plan_retrieval`
   Builds a standard LangGraph tool-call plan for any missing context areas.
3. `tool_node`
   Executes LangChain-style tools through a `ToolNode`. Each tool wrapper is backed by `runagents.Agent().call_tool(...)`, so deploy-time tool selection still routes to the platform-registered tools.
4. `integrate_tool_outputs`
   Normalizes tool results into briefing context and evidence.
5. `synthesize_brief`
   Uses `ChatOpenAI` through the RunAgents LLM gateway to turn the gathered context into the final executive briefing.

## How models are called
- The graph creates a `ChatOpenAI` client with `LLM_MODEL`.
- RunAgents injects `OPENAI_BASE_URL` and `OPENAI_API_KEY`, so LangChain routes through the platform LLM gateway automatically.
- The final response is generated in the `synthesize_brief` node.

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

## Deployment intent
Use this as a governed starting point for executive morning briefs, staff prep, and leadership decision digests. The example is designed to show the long-term enterprise pattern: standard LangGraph tool usage for retrieval, backed by RunAgents-managed tools for policy, approvals, identity propagation, and audit.
