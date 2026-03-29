# Chief of Staff Agent

A LangGraph-based executive operations agent that acts like a proactive chief of staff across calendar, inbox, docs, chat, tasks, CRM, and WhatsApp.

## Why teams deploy this
Senior operators and executives do not need another generic chatbot. They need something that can gather context from the systems they already live in, tell them what matters, and tee up the next move without losing control.

This example is built for exactly that. It shows how to use RunAgents to create a high-trust, multi-surface assistant that can:
- prepare a sharp morning priorities brief
- brief a leader before a key meeting
- turn meeting notes into follow-through
- summarize customer interactions and account risk
- produce end-of-day or weekly digests
- prepare approval-ready actions for email, Slack or Teams, tasks, CRM, calendar, and WhatsApp

## What the agent will do for a user
The agent starts by understanding the mode of the request. It then decides which evidence is missing, calls the right tools, integrates the results, and produces a response that feels like a real chief of staff deliverable instead of a vague summary.

Depending on the request, it can return:
- the top things to focus on today
- prep notes for an upcoming meeting
- a clean recap with actions, owners, and follow-up drafts
- a concise customer interaction summary with risk and next-step guidance
- an end-of-day summary with what moved, what slipped, and what should happen next
- approval-ready actions for anything that would write into another system

## What makes this example different
This example is deliberately opinionated about governance.

It treats reads, summaries, and draft preparation as the default autonomous behavior. When the user asks for a write action such as sending an email, posting to team chat, updating a tracker, changing calendar state, or messaging through WhatsApp, the agent prepares the exact action and routes it into an approval-ready queue.

That is the correct operating model for a real chief of staff assistant:
- proactive on context gathering
- disciplined on execution
- explicit about what still needs approval

## What it includes
- Suggested model: `gpt-4.1`
- Required tools: `calendar`, `email`, `drive`, `team-chat`, `project-tracker`, `meeting-notes`
- Recommended tools: `crm`, `knowledge-base`, `whatsapp`, `imessage`
- Authoring pattern: `LangGraph agent loop + ToolNode`
- Access intent: `authenticated`

## How the workflows map to enterprise work
### Morning priorities
The agent pulls schedule, inbox, task, collaboration, and customer signals to answer:
- what matters today
- what needs prep
- what follow-ups are overdue
- what should move before noon

### Meeting prep
The agent gathers calendar context, notes, docs, team chatter, and account context to produce:
- meeting objective
- attendee and stakeholder context
- previous commitments
- unresolved decisions
- suggested talking points

### Meeting follow-up
The agent consolidates notes, decisions, and open tasks to produce:
- recap
- action items
- owners
- deadlines
- draft follow-up messages
- approval-ready write actions for tasks or outbound messaging

### Customer interaction summary
The agent combines CRM, inbox, team chat, project, and notes context to produce:
- customer sentiment
- current risk
- promises already made
- internal blockers
- recommended next move

### End-of-day or weekly digest
The agent turns the operating noise of the day into:
- what changed
- what slipped
- who needs follow-up
- what the leader should do next
- which draft actions should be approved now

## How tools are used
The graph defines standard LangChain tools with `@tool`, but each tool wrapper calls `runagents.Agent().call_tool(...)` underneath. That means all real connectivity still stays inside RunAgents:
- deploy-time tool binding
- policy enforcement
- delegated-user identity where needed
- tracing and audit
- approval routing

The example is intentionally vendor-agnostic. The graph expects capability tools such as:
- `email` instead of Gmail-only code
- `drive` instead of Google Drive-only code
- `team-chat` instead of Slack-only code

That lets the same example deploy against different enterprise stacks as long as the workspace registers those tools.

## How approvals are intended to work
This example is designed around a strong enterprise default:
- reads are allowed
- summaries are allowed
- drafts are allowed
- writes should be `approval_required`

The best default approver for this agent is the same user who invoked it. That fits the actual chief of staff use case well because most writes are delegated-user actions such as:
- send this email from me
- post this update for me
- create these follow-up tasks for me
- move this meeting for me
- send this summary to my WhatsApp lane

A strong deployment will deliver those approvals through one or more approval connectors such as:
- Slack
- WhatsApp via webhook bridge
- iMessage via webhook bridge
- local RunAgents UI fallback

## WhatsApp in this example
WhatsApp is included as the premium mobile lane for this agent.

That is useful for:
- morning brief delivery
- urgent follow-up summaries
- lightweight executive commands
- approval prompts when the user is away from their desk

The example does not assume WhatsApp is the system of record. It treats it as an interaction and approval surface layered on top of the real enterprise systems.

## What happens during a run
1. `ingest_request`
   Parses the incoming message. If the caller sends JSON, the graph can accept seeded context such as schedule, inbox threads, notes, customer context, or requested delivery lanes.
2. `reasoning_agent`
   Uses the model as the orchestrator. It decides whether enough evidence is already present or whether one or more tools should be called.
3. `tool_node`
   Executes the selected tools through a LangGraph `ToolNode`. Every tool is still backed by RunAgents-managed routing.
4. `integrate_tool_outputs`
   Normalizes retrieved results into the chief-of-staff dossier and records evidence.
5. `finalize_response`
   Produces a polished operational output that includes the briefing plus any approval-ready actions that should happen next.

## Example input
Plain text works:

```text
Give me my chief of staff morning brief for today and prepare any follow-ups I should approve over WhatsApp.
```

Structured JSON works too:

```json
{
  "mode": "morning-priorities",
  "objective": "Prepare my morning brief and line up anything that needs my approval.",
  "delivery_lanes": ["whatsapp", "slack"],
  "schedule": [{"title": "Board prep review"}],
  "emails": [{"subject": "Renewal risk - Northwind"}],
  "tasks": [{"title": "Close Q2 operating plan", "status": "at_risk"}],
  "customer": [{"account": "Northwind", "summary": "Asking for escalation support"}]
}
```

## What a strong deployment looks like
For a real deployment, bind the capability tools to enterprise systems you already trust:
- `calendar` -> Google Calendar or Outlook Calendar
- `email` -> Gmail or Outlook
- `drive` -> Google Drive or OneDrive
- `team-chat` -> Slack or Teams
- `project-tracker` -> Jira, Linear, Asana, or similar
- `meeting-notes` -> internal note system or transcript pipeline
- `crm` -> Salesforce, HubSpot, or similar
- `whatsapp` -> mobile delivery or approval lane bridge

That gives the model enough grounded evidence to act like a serious operator instead of a toy assistant.

## Deploy from CLI
If your RunAgents CLI is not configured yet:

```bash
runagents config set endpoint https://<your-runagents-endpoint>
runagents config set api-key <your-api-key>
runagents config set namespace <your-workspace-namespace>
```

Then deploy this example from the catalog directory:

```bash
cd catalog/agents/chief-of-staff

runagents deploy \
  --name chief-of-staff-agent \
  --file src/agent.py \
  --tool calendar \
  --tool email \
  --tool drive \
  --tool team-chat \
  --tool project-tracker \
  --tool meeting-notes \
  --tool crm \
  --tool knowledge-base \
  --tool whatsapp \
  --model openai/gpt-4.1
```

What this does:
- uploads `src/agent.py` as the agent source
- binds the core RunAgents tools used by the workflow
- enables CRM, knowledge, and WhatsApp as richer context and delivery lanes
- sets the default reasoning model to `gpt-4.1`

## Deployment intent
Use this as the flagship example for a modern executive operations agent: grounded, channel-aware, mobile-friendly, and governance-safe. It shows the stronger enterprise pattern where the model can reason over many sources, while every real tool call still stays inside RunAgents-managed routing and approval policy.
