---
name: runagents-identity-provider-setup
description: Use when configuring identity providers for RunAgents. Helps map JWT claims, preserve end-user identity across the runtime, and ensure delegated-user tools, approvals, and audit trails all line up with the right subject identity.
---

# RunAgents Identity Provider Setup

Use this skill when a RunAgents deployment needs client authentication and end-user identity propagation.

## Use this skill for

- setting up JWT-based identity providers
- choosing the right user claim for subject identity
- validating that end-user identity reaches runs and tools correctly
- making delegated-user OAuth and approvals work with the right user context
- debugging identity mismatches across client, runtime, and tool calls

## Workflow

1. Start from the client identity source.
   Determine:
   - JWT issuer
   - JWKS endpoint
   - subject claim to use
   - domain or tenant constraints if needed

2. Pick a stable user identity.
   Use a claim that behaves well operationally across approvals, delegated auth, and audit history.

3. Validate propagation end to end.
   Check that the platform turns the incoming identity into the right runtime subject and forwards it to downstream tools where appropriate.

4. Align identity with user-scoped workflows.
   This especially matters for:
   - OAuth consent
   - approval grants tied to a user
   - audit trails and run history

5. Test with a real tool call, not only a successful identity-provider create call.

## Strong defaults

- Prefer stable business identities when available.
- Keep issuer and claim mapping explicit in docs and examples.
- Treat identity propagation as a runtime contract, not just a login feature.

## Example prompt

Use `$runagents-identity-provider-setup` to configure delegated-user identity for this workspace and make sure approvals and Google OAuth both resolve to the correct end user.
