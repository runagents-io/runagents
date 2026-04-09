---
name: runagents-oauth-consent-debugging
description: Use when delegated-user OAuth or consent flows are failing in RunAgents. Helps distinguish consent from approvals, validate scopes and callbacks, and trace whether the stored token is actually sufficient for the intended tool action.
---

# RunAgents OAuth Consent Debugging

Use this skill when a RunAgents workflow is blocked on delegated-user OAuth or is behaving as though the stored token is not usable.

## Use this skill for

- `CONSENT_REQUIRED` loops
- callback misconfiguration
- scope mismatches
- read-only tokens used against write actions
- debugging the difference between a successful consent and a successful business action

## Workflow

1. Separate consent from approval first.
   Consent means the user must authorize the tool.
   Approval means a reviewer must approve a governed action.

2. Inspect the requested scopes and the intended action.
   The scope set must be sufficient for the action the tool is attempting.

3. Validate the callback path.
   Check provider configuration, redirect URI allow-listing, and whether the platform actually receives and stores the token.

4. Confirm the stored token is good enough for the real operation.
   A token may exist and still be too narrow for the attempted write.

5. Re-test the end-to-end action after renewing consent.
   The workflow is only fixed when the actual downstream business action succeeds.

## Strong defaults

- Do not confuse a valid token with a sufficient token.
- Keep scopes narrow but action-complete.
- Use Google Workspace write flows as a reference case for scope debugging.

## Example prompt

Use `$runagents-oauth-consent-debugging` to figure out why this RunAgents tool still returns consent or permission errors even though the user already authorized Google access.
