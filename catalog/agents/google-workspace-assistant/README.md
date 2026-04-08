# Google Workspace Assistant

A LangGraph-based Google-first work assistant that operates across Gmail, Google Calendar, Google Drive, Google Docs, Google Sheets, Google Tasks, and Google Keep.

## Why teams deploy this

Most people working inside Google Workspace already have the right context, but it is scattered across inbox threads, calendar events, docs, spreadsheets, task lists, and notes. This catalog blueprint is meant to give them one assistant that can gather that context quickly, reason over it, and return something useful without pretending disconnected summaries are enough.

Use it when you want an assistant that can:
- triage the day from Gmail and Calendar
- pull supporting context from Drive, Docs, and Sheets
- consolidate action items from Tasks and Keep
- create explicit Google Calendar events when the timing details are clear
- draft approval-ready replies, follow-ups, or document changes when a write should stay gated
- stay inside RunAgents governance instead of bypassing policy and audit

## Tool mapping

This catalog entry follows the existing RunAgents catalog pattern: the manifest uses normalized tool names, and you bind those slots to Google-backed tools at deploy time.

- `email` -> Gmail
- `calendar` -> Google Calendar
- `drive` -> Google Drive
- `docs` -> Google Docs
- `sheets` -> Google Sheets
- `tasks` -> Google Tasks
- `keep` -> Google Keep

## What the agent will do for a user

The assistant accepts plain text or structured JSON. It starts with the user’s objective, checks whether enough context is already present, then decides which Google Workspace tools to call. It is strongest when the user needs one response assembled from several Google surfaces instead of a single isolated API call.

A typical result includes:
- the relevant facts pulled from Gmail, Calendar, Docs, Sheets, Tasks, or Keep
- the important gaps or blockers that still matter
- the recommended next step
- approval-ready draft actions when a write would be required

## What it includes

- Suggested model: `gpt-4.1`
- Required tools: `email`, `calendar`, `drive`, `docs`, `sheets`, `tasks`, `keep`
- Authoring pattern: `LangGraph agent loop + ToolNode`

## What happens during a run

1. `ingest_request`
   Parses plain text or JSON and seeds whatever Google Workspace context the caller already has.
2. `reasoning_agent`
   Uses the model to decide whether the current context is enough or whether Gmail, Calendar, Drive, Docs, Sheets, Tasks, or Keep should be queried.
3. `tool_node`
   Executes explicit LangGraph tools such as `gmail_list_messages`, `calendar_list_events`, `calendar_create_event`, `drive_list_files`, `docs_get_document`, `sheets_read_range`, `tasks_list_tasks`, and `keep_list_notes`.
4. `integrate_tool_outputs`
   Normalizes tool results back into one shared assistant dossier.
5. `finalize_response`
   Produces the best possible grounded answer if the tool budget is exhausted.

## How tools are called

Each tool wrapper calls `runagents.Agent().call_tool(...)` with an explicit HTTP path and method, so the agent owns the task semantics while deploy-time tool binding still controls where the request goes. That keeps identity propagation, policy checks, approvals, and audit inside RunAgents instead of inside example code.

Examples:

- `gmail_list_messages` -> `GET /gmail/v1/users/me/messages`
- `gmail_get_message` -> `GET /gmail/v1/users/me/messages/{messageId}`
- `calendar_list_events` -> `GET /calendar/v3/calendars/primary/events`
- `calendar_create_event` -> `POST /calendar/v3/calendars/primary/events`
- `drive_list_files` -> `GET /drive/v3/files`
- `docs_get_document` -> `GET /v1/documents/{documentId}`
- `sheets_get_spreadsheet` -> `GET /v4/spreadsheets/{spreadsheetId}`
- `sheets_read_range` -> `GET /v4/spreadsheets/{spreadsheetId}/values/{range}`
- `tasks_list_tasklists` -> `GET /tasks/v1/users/@me/lists`
- `tasks_list_tasks` -> `GET /tasks/v1/lists/{tasklistId}/tasks`
- `keep_list_notes` -> `GET /v1/notes`

## Example prompts

Plain text:

```text
Give me a Google Workspace morning brief and tell me what needs my attention first.
```

Explicit write:

```text
Create a 30 minute calendar event titled "Policy Test" on 2026-04-09T14:00:00-04:00 and invite alex@example.com.
```

Structured JSON:

```json
{
  "objective": "Prepare me for today's customer review and tell me what follow-up I owe.",
  "emails": [{"subject": "Customer review prep", "summary": "Need Q2 usage and renewal status"}],
  "calendar": [{"title": "Customer review", "status": "today 2pm"}],
  "docs": [{"title": "Account plan", "summary": "Expansion path depends on usage trend"}],
  "tasks": [{"title": "Send renewal follow-up", "status": "open"}]
}
```

## What a strong deployment looks like

This blueprint is strongest when the user can access Google Workspace through delegated-user connectors:

- Gmail for inbox and follow-up context
- Google Calendar for the daily schedule
- Google Drive and Docs for document context
- Google Sheets for planning and operational data
- Google Tasks for tracked follow-through
- Google Keep for capture notes and reminders

That combination lets the assistant answer with actual workspace context instead of generic productivity advice.

## Deploy from CLI

If your RunAgents CLI is not configured yet:

```bash
runagents config set endpoint https://<your-runagents-endpoint>
runagents config set api-key <your-api-key>
runagents config set namespace <your-workspace-namespace>
```

Then deploy this example:

```bash
cd catalog/agents/google-workspace-assistant

runagents deploy \
  --name google-workspace-assistant-agent \
  --file src/agent.py \
  --tool email \
  --tool calendar \
  --tool drive \
  --tool docs \
  --tool sheets \
  --tool tasks \
  --tool keep \
  --model openai/gpt-4.1
```

## Deployment intent

Use this as the default Google Workspace assistant when you want one agent to work across Gmail, Calendar, Drive, Docs, Sheets, Tasks, and Keep instead of forcing the user to think in per-API silos. Keep explicit write methods such as `calendar_create_event` behind policy or approval until the workflow is tuned for your environment.
