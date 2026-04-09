---
name: runagents-model-provider-setup
description: Use when configuring model providers and gateway behavior for RunAgents. Helps choose the right provider setup, keep model routing explicit, and validate that agent roles and provider credentials line up correctly before deployment.
---

# RunAgents Model Provider Setup

Use this skill when wiring LLM providers into RunAgents.

## Use this skill for

- registering model providers
- choosing provider and model roles for an agent
- configuring gateway-backed inference cleanly
- debugging model-provider mismatches after deployment
- validating that the runtime sees the expected model and provider wiring

## Workflow

1. Start from the agent workload.
   Determine whether the workflow needs:
   - low-latency general responses
   - tool-using reasoning
   - higher-quality planning
   - specific model-family compatibility

2. Register the provider cleanly.
   Keep credentials out of agent code and rely on the platform-managed model provider.

3. Make model roles explicit.
   If the agent uses separate roles, document which provider and model serve each one.

4. Validate through the runtime.
   Confirm that the deployed agent actually uses the configured gateway path and role mapping.

5. Separate model issues from tool or approval issues.
   A model-provider problem should not be misdiagnosed as a tool contract or policy problem.

## Strong defaults

- Prefer explicit model-role configuration over hidden defaults in production.
- Keep provider configuration in the platform, not in agent source.
- Validate one real agent run after changes.

## Example prompt

Use `$runagents-model-provider-setup` to wire the right provider and model roles for this RunAgents agent and tell me how to validate the deployed configuration.
