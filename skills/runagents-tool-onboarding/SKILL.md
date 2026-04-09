---
name: runagents-tool-onboarding
description: Use when registering or updating RunAgents tools. Helps define capabilities precisely, choose the right auth model, keep OAuth scopes narrow, and validate that the tool contract matches the agent workflow before deployment.
---

# RunAgents Tool Onboarding

Use this skill when a RunAgents agent needs a new tool or an existing tool contract needs to be corrected.

## Use this skill for

- registering a new API-backed tool
- adding or narrowing capabilities
- choosing OAuth vs API key vs delegated auth
- fixing a tool that is too broad, too narrow, or missing a required write operation
- validating scopes and capabilities for governed writes

## Workflow

1. Start from the agent workflow, not the API docs.
   Figure out what the agent actually needs to do.
   Example: "create calendar event" means the tool needs a matching write capability and a write-capable OAuth scope.

2. Define capabilities precisely.
   Prefer exact method + path combinations over broad wildcards.
   Example:
   - `GET /calendar/v3/calendars/primary/events`
   - `POST /calendar/v3/calendars/primary/events`

3. Choose the narrowest viable auth model.
   - API key for server-to-server tools
   - OAuth for delegated-user tools
   - delegated user auth when the action must run on behalf of a person

4. Keep OAuth scopes narrow and aligned to the capabilities.
   Do not ask for write scopes when the tool is read-only.
   Do not expect a read-only token to succeed on write operations.

5. Validate the whole tool contract.
   Check:
   - base URL
   - auth configuration
   - capabilities
   - scopes
   - request/response schemas if applicable

## Strong defaults

- Least privilege beats convenience.
- If the tool performs writes, line up all three layers: capability, scope, and approval policy.
- When debugging, do not confuse tool capability errors with approval or consent errors.

## Example prompt

Use `$runagents-tool-onboarding` to register a Google Calendar tool that supports event creation safely with delegated OAuth and the minimum required capabilities.
