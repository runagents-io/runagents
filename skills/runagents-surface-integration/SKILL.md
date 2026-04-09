---
name: runagents-surface-integration
description: Use when connecting RunAgents to a user-facing interface such as a web app, WhatsApp, Slack, an internal portal, or a custom client. Helps preserve end-user identity, handle approvals and consent correctly, and make resumed execution visible to the user.
---

# RunAgents Surface Integration

Use this skill when an agent is not only an internal backend workflow, but part of a real user-facing interface.

## Core idea

The interface can be anywhere.

RunAgents should be able to sit behind:

- web applications
- WhatsApp
- Slack
- internal portals
- custom clients

The governed runtime stays the same. What changes is the surface layer and how it carries identity, approvals, consent, and final responses.

## Use this skill for

- designing a new messaging or app surface
- wiring a WhatsApp or Slack experience to RunAgents
- preserving end-user identity across the surface boundary
- making approval and consent states visible to the user
- ensuring resumed work posts the result back to the originating surface

## Workflow

1. Identify the surface contract.
   Determine:
   - incoming user identity
   - conversation or session identifier
   - response delivery channel
   - whether the surface supports asynchronous updates

2. Preserve end-user identity explicitly.
   The runtime should know which user the agent is acting for, especially when tool auth and approvals are user-scoped.

3. Design for pause and resume.
   The surface should handle:
   - approval required
   - consent required
   - resumed completion after a background approval decision

4. Validate both runtime and surface behavior.
   Confirm:
   - run resumed in governance
   - tool action succeeded
   - final success or failure was delivered back to the original interface

5. Keep operator and user language distinct.
   Operators care about policy and runtime state.
   Users care about whether the action completed.

## Strong defaults

- WhatsApp is a strong example because it forces asynchronous approval and completion handling.
- If the interface cannot wait synchronously, design it as a pause/resume surface from the start.
- Approval and consent should be visible as different user states.

## Example prompt

Use `$runagents-surface-integration` to design a WhatsApp-based RunAgents experience where the same governed workflow could later be moved to Slack or an internal web app without changing the runtime contract.
