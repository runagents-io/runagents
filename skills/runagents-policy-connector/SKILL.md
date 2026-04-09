---
name: runagents-policy-connector
description: Use when exposing RunAgents policy information to another system or building a custom policy-focused integration. Helps model the right policy data, separate active posture from stale bindings, and present allow, deny, and approval-required behavior clearly in external tools.
---

# RunAgents Policy Connector

Use this skill when an external system needs a trustworthy view of RunAgents policy state.

## Use this skill for

- building a policy dashboard outside the RunAgents console
- exporting policy and policy-binding state into another control plane
- showing which agents or service identities are governed by which policies
- separating active policy usage from stale or deleted-agent references
- designing policy-related APIs or sync jobs that remain understandable to operators

## Workflow

1. Start from the operator question.
   Decide whether the external system needs to answer:
   - what is allowed
   - what is denied
   - what requires approval
   - which agents or identities are bound to which policy
   - whether the referenced resources are still active

2. Model active posture first.
   Do not mix stale bindings, deleted agents, and current policy usage into one view.

3. Keep policy semantics explicit.
   A connector should preserve the difference between:
   - allow
   - deny
   - approval-required

4. Validate against real workspace data.
   Check that the external view matches the live platform state for at least a few concrete agents and tools.

5. Design for auditability.
   The connector should make it easier to explain why an action was allowed, denied, or routed to approval.

## Strong defaults

- Prefer active-agent views by default.
- Treat stale bindings as a maintenance bucket, not part of normal policy usage.
- Keep policy evaluation outcomes legible to non-authz specialists.

## Example prompt

Use `$runagents-policy-connector` to design a connector that exposes active RunAgents policies, bindings, and approval-required behavior to an internal governance dashboard.
