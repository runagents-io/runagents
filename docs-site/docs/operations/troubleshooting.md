---
title: Troubleshooting
description: Common issues when using RunAgents and how to resolve them, including agent status problems, permission errors, OAuth issues, and build failures.
---

# Troubleshooting

This page covers common issues you may encounter when using RunAgents and how to resolve them.

---

## Agent Issues

### Agent stuck in "Pending" status

The agent was created but has not transitioned to "Running."

**Possible causes:**

- **Agent image is not accessible** -- If you deployed custom agent code, verify the container image was built successfully. Check the build status via **Agents** > your agent > **Overview**.
- **Required tools do not exist** -- The agent references tools that have not been registered. Verify all tools listed in the agent's `requiredTools` are registered on the platform.
- **Required model provider does not exist** -- The agent references a model provider that has not been created. Check the **Models** page to verify.
- **Event log has details** -- Navigate to the agent's detail page and check the event log for specific error messages.

!!! tip "Check the event log first"

    The agent's event log is the most reliable source of information about why an agent is not starting. Most issues include a descriptive error message.

---

## Permission Errors

### 403 Forbidden on tool calls

The agent attempted to call a tool but was denied.

**Possible causes:**

- **No policy binding exists** -- The agent does not have a policy granting access to the target tool.
    - For **Open** tools: verify the tool is listed in the agent's required tools. Auto-binding creates the policy on deploy.
    - For **Restricted** tools: you must create a policy and policy binding explicitly. Go to **Approvals** or use the API.
    - For **Critical** tools: an approval is required for each access. Check the **Approvals** page for pending requests.

- **Capability mismatch** -- The tool declares specific capabilities, and the agent's request does not match any of them. For example, the agent sends a `DELETE` request but the tool only allows `GET` and `POST`. Check the tool's registered capabilities.

- **Deny rule takes precedence** -- A deny rule in a policy is overriding an allow rule. Review the policies bound to the agent.

**How to diagnose:**

1. Go to **Approvals** to see if there is a pending request for this agent + tool combination
2. Check the tool's access control mode (Open, Restricted, or Critical)
3. Review the tool's capabilities to ensure the requested operation is allowed
4. Review policies bound to the agent's service account

### APPROVAL_REQUIRED response

The agent called a tool that has `requireApproval` enabled.

**What to do:**

1. An access request has been automatically created
2. If the agent is in a run, the run has been paused (`PAUSED_APPROVAL`)
3. An admin must approve the request on the **Approvals** page
4. After approval, the run resumes automatically

!!! info "Approvals are per-request for Critical tools"

    For tools with Critical access mode, each access requires a separate approval. Previously approved access expires after the configured TTL.

---

## OAuth Issues

### CONSENT_REQUIRED response

The tool uses OAuth2 and the end user has not authorized access yet.

**What to do:**

1. The response includes an `authorization_url`
2. Your client application should redirect the user to that URL
3. The user completes the consent screen at the OAuth provider (e.g., Google)
4. After consent, retry the original request -- the platform now has a valid token

See [OAuth & Consent](../concepts/oauth-consent.md) for the full flow.

### OAuth callback fails

The OAuth callback URL did not receive the authorization code, or the code exchange failed.

**Possible causes:**

- **Callback URL not configured** -- Verify that the RunAgents OAuth callback URL is set in your platform configuration.
- **Redirect URI not whitelisted** -- The OAuth provider (e.g., Google, Slack) must have the RunAgents callback URL in its list of allowed redirect URIs. Check the provider's application settings.
- **Invalid client credentials** -- The `client_id` or `client_secret` in the tool's credentials are incorrect. Update them via the console or API.
- **State signature mismatch** -- The HMAC-signed state parameter failed verification. This can happen if the signing key changed between the authorization request and the callback. Ensure the signing key is persistent.

---

## LLM Gateway Issues

### LLM Gateway returns 404 / model not found

The agent requested a model that is not registered on the platform.

**What to do:**

1. Go to **Models** in the console
2. Verify that the model name the agent uses (e.g., `gpt-4o`, `claude-3-opus`) appears in a registered model provider's model list
3. The model ID must match exactly -- check for typos or version mismatches
4. If the model provider does not exist, create one with the correct provider type and model list

### LLM Gateway returns 502 / provider unreachable

The LLM provider's API endpoint is not responding.

**Possible causes:**

- The provider is experiencing an outage (check their status page)
- The provider's URL in the model provider configuration is incorrect
- Network connectivity issues between the platform and the provider

---

## Tool Issues

### Tool status shows "Unavailable"

The platform periodically probes tool endpoints. An "Unavailable" status means the probe failed.

**What to check:**

- **Base URL is correct** -- Verify the tool's registered URL points to a live endpoint
- **Endpoint is reachable** -- The tool's API must be accessible from the platform's network
- **Probe details** -- Check `lastProbeTime` and `probeLatencyMs` in the tool's details to understand when the last successful probe occurred

!!! note "Probes are non-intrusive"

    The platform probes tool health using lightweight requests. An "Unavailable" status does not necessarily mean the tool is down -- it may indicate a network or DNS issue between the platform and the tool.

---

## Build Issues

### Build fails

The platform was unable to build a container image from your agent code.

**How to diagnose:**

1. Check the build status and logs:

    ```bash
    curl https://your-platform/api/builds/{build_id}
    ```

2. **Common issues:**
    - **Missing dependencies** -- The platform detected imports but could not resolve them to packages. Add a `requirements.txt` to your agent code.
    - **Invalid entry point** -- The platform could not determine which file to run. Ensure your main file is clearly identifiable (e.g., `main.py`, `app.py`).
    - **Unsupported language features** -- The build environment supports Python. Check that your code is compatible.
    - **Syntax errors** -- The code has syntax errors that prevent the build from completing.

---

## Run Issues

### Run stuck in PAUSED_APPROVAL

The run is waiting for admin approval on a tool access request.

**What to do:**

1. Go to **Approvals** in the console
2. Find the pending request for the run
3. Approve or reject the request
4. If approved, the run resumes automatically within a few seconds

### Run failed unexpectedly

Check the run's event log for error events:

=== "Console"

    Navigate to **Agents** > your agent > **Runs** tab > select the run > view the event timeline

=== "API"

    ```bash
    curl https://your-platform/runs/{run_id}/events
    ```

Look for `ERROR` events, which include details about what went wrong.

---

## Getting More Help

!!! success "Still stuck? We are here to help."

    If you have tried the steps above and are still experiencing issues, contact us:

    - **Email**: [try@runagents.io](mailto:try@runagents.io)
    - **Existing customers**: [support@runagents.io](mailto:support@runagents.io)
    - **GitHub**: [github.com/runagents](https://github.com/runagents) -- open an issue for bugs or feature requests

    Include the following in your message for fastest resolution:

    - Your agent name and the affected run ID (if applicable)
    - The error message or response body you received
    - Steps to reproduce the issue
