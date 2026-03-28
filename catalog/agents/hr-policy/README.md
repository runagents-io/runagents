# HR Policy Agent

A LangGraph-based people operations agent that answers HR policy questions with grounded references and safe escalation guidance.

## What it includes
- Suggested model: `gpt-4.1-mini`
- Required tools: `hris`, `knowledge-base`
- Default policy: `hr-readonly`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## Graph flow
1. `ingest_request`
   Parses plain text or structured JSON and seeds policy references or employee context when those are already available.
2. `reasoning_agent`
   Uses the model to decide whether more handbook or HRIS context is needed before answering.
3. `tool_node`
   Executes standard LangChain `@tool` wrappers backed by `runagents.Agent().call_tool(...)`.
4. `integrate_tool_outputs`
   Normalizes policy and employee context and loops back into the reasoning step.
5. `finalize_answer`
   Safety fallback if the tool budget is exhausted.

## How models are called
- The example uses `ChatOpenAI` with `LLM_MODEL`.
- RunAgents injects the OpenAI-compatible env vars, so the graph routes through the platform LLM gateway automatically.
- The model decides when more policy context is needed and when the answer is grounded enough to return.

## How tools are called
- The example uses standard LangChain `@tool` wrappers.
- Each wrapper calls `runagents.Agent().call_tool(...)` so deploy-time tool selection still controls the actual tool endpoints.
- That preserves policy, audit, and delegated identity handling on the tool path.

## Example input
Plain text:

```text
What is the parental leave policy for salaried employees in the US?
```

Structured JSON:

```json
{
  "question": "What is the parental leave policy for salaried employees in the US?",
  "employee_context": [{"name": "Employee", "location": "US", "employment_type": "Salaried"}]
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
cd catalog/agents/hr-policy

runagents deploy \
  --name hr-policy-agent \
  --file src/agent.py \
  --tool hris \
  --tool knowledge-base \
  --model openai/gpt-4.1-mini
```

## Deployment intent
Use this as a safe starting point for employee-facing HR policy helpdesks, benefits guidance, and handbook question workflows.
