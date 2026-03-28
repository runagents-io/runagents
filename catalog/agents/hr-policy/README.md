# HR Policy Agent

A LangGraph-based people operations agent that answers HR policy questions with grounded references and safe escalation guidance.

## Why teams deploy this
Employees ask the same benefits and policy questions repeatedly, but HR teams still need those answers to be grounded, careful, and easy to audit. This example shows how to answer common policy questions quickly without pretending the model should improvise on sensitive rules.

Use it when you want an agent that can:
- answer handbook and benefits questions with cited internal context
- pull employee-specific context when it is appropriate to do so
- reduce repetitive policy triage for HR and people operations teams
- escalate cleanly when a question needs a human decision rather than a generated answer

## What the agent will do for a user
A user can ask a policy question in plain language, such as parental leave, eligibility, holidays, or benefits coverage. The agent will inspect what it already knows, decide what policy or HRIS context it needs, gather that context, and return a careful answer.

A typical result includes:
- a direct answer to the employee's question
- the policy basis or handbook context behind the answer
- any employee-specific qualifiers it can safely infer
- uncertainty or missing information when the answer is not fully grounded
- a recommendation to escalate to HR when the case is sensitive or ambiguous

## What it includes
- Suggested model: `gpt-4.1-mini`
- Required tools: `hris`, `knowledge-base`
- Default policy: `hr-readonly`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## What happens during a run
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

## Why the tools matter
- `hris`: provides employee or employment context when the question depends on role, location, or worker type
- `knowledge-base`: grounds the answer in handbook pages, benefits docs, and official policy references

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

## What a strong deployment looks like
This example works best when it can see:
- official handbook and benefits documentation
- employee metadata from the HRIS that affects eligibility or policy interpretation

That lets it stay useful for common questions while remaining grounded and conservative on sensitive cases.

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
