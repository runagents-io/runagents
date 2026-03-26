# Executive Briefing Agent

A LangGraph-based leadership productivity agent that assembles a concise daily briefing from meetings, project updates, stakeholder signals, and internal reference context.

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `calendar`, `project-tracker`, `knowledge-base`, `chat`
- Default policies: `leadership-readonly`, `internal-docs-readonly`
- Authoring pattern: `LangGraph`

## Graph flow
1. `ingest_request`
   Parses the incoming message. If the caller sends JSON, the graph can use inline `meetings`, `project_updates`, `reference_notes`, and `stakeholder_notes` as seed context.
2. `gather_calendar`
   Uses the RunAgents-managed `calendar` tool when meeting context was not already supplied.
3. `gather_project_signals`
   Pulls delivery risk and decision context from `project-tracker`.
4. `gather_reference_notes`
   Pulls background context from `knowledge-base`.
5. `gather_stakeholder_signals`
   Pulls sentiment and escalation signals from `chat`.
6. `synthesize_brief`
   Uses `ChatOpenAI` through the RunAgents LLM gateway to turn the gathered context into the final executive briefing.

## How models are called
- The graph creates a `ChatOpenAI` client with `LLM_MODEL`.
- RunAgents injects `OPENAI_BASE_URL` and `OPENAI_API_KEY`, so LangChain routes through the platform LLM gateway automatically.
- The final response is generated in the `synthesize_brief` node.

## How tools are called
- The graph uses `runagents.Agent().call_tool(...)` inside dedicated retrieval nodes.
- Each retrieval node sends a best-effort briefing payload to the matching RunAgents-managed tool.
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
Use this as a governed starting point for executive morning briefs, staff prep, and leadership decision digests. The example is designed to show the long-term enterprise pattern: retrieval nodes for governed context gathering, then a model synthesis node for the final brief.
