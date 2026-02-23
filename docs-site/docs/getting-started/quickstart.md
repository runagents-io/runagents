---
title: Quickstart
description: Deploy your first AI agent in 5 minutes using the RunAgents console.
---

# Quickstart

Deploy your first agent in 5 minutes using the RunAgents console. No code to write, no configuration to manage — the platform provides a sample agent and built-in tools to get you started instantly.

!!! info "Prerequisites"

    You need a RunAgents account. If you do not have one yet, email [try@runagents.io](mailto:try@runagents.io) to request trial access.

---

## Step 1: Log In to the Console

Open the RunAgents console at your platform URL and log in with your credentials.

When the platform is new or empty, the **Dashboard** displays a welcome screen with a prominent call to action.

---

## Step 2: Deploy the Hello World Agent

Click **"Deploy Hello World Agent"** on the dashboard hero card.

Alternatively, navigate to **Agents** in the sidebar and click **"+ New Agent"**.

The platform automatically seeds two starter resources for you:

| Resource | Description |
|---|---|
| **Echo Tool** | A built-in tool that echoes back any message you send it. No external API keys needed. |
| **Playground LLM** | A pre-configured LLM provider (OpenAI gpt-4o-mini) for testing. |

!!! note

    The starter resources are created automatically the first time you deploy the Hello World agent. They are labeled as demo resources and can be replaced with real services later.

---

## Step 3: Review the Deploy Wizard

The deploy wizard has three steps:

### Upload

The sample agent code loads automatically. It is a simple agent that:

- Calls the **Echo Tool** to send and receive messages
- Uses the **Playground LLM** to generate responses

The platform analyzes the code in real time and detects the tools and LLM providers it uses.

### Wire

The wiring step shows what the analysis found:

- **Detected tools** are matched to registered tools on the platform (Echo Tool)
- **Detected LLM usage** is matched to available model providers (Playground LLM)
- **Agent name** is pre-filled as `hello-world`

For the Hello World agent, everything is pre-wired. All indicators should show green.

### Deploy

Review the summary and click **Deploy**. The platform:

1. Creates the agent with its configuration
2. Sets up a service account for the agent
3. Auto-creates policies that allow the agent to call its required tools
4. Starts the agent

---

## Step 4: View Your Agent

After deployment, you are redirected to the **Agent Detail** page. Here you can see:

- **Status**: The agent transitions from `Pending` to `Running`
- **Overview**: Configuration, required tools, and LLM settings
- **Runs**: A timeline of all invocations once the agent starts receiving requests

---

## What Just Happened?

Here is what RunAgents did behind the scenes when you clicked Deploy:

1. **Code analysis** -- The platform scanned the sample code using AST parsing and pattern detection. It identified outbound HTTP calls to the Echo Tool and LLM gateway usage.

2. **Tool wiring** -- The detected tool calls were matched to the registered Echo Tool. The agent was configured with the correct tool URLs as environment variables.

3. **LLM wiring** -- The detected model usage was matched to the Playground LLM provider. The agent was configured with the LLM gateway URL and model settings.

4. **Policy auto-binding** -- Since the Echo Tool is configured with open access (no approval required), the platform automatically created access policies allowing the `hello-world` agent to call it.

5. **Agent deployment** -- The agent was deployed with its service account, environment configuration, and networking rules. All outbound traffic from the agent flows through the platform's security layer.

The agent is now live. Any request it makes to the Echo Tool is automatically:

- Checked against the access policy
- Enriched with the correct authentication credentials
- Forwarded with the end-user's identity

---

## Next Steps

Now that you have a running agent, explore further:

- **Register your own tools** -- Add external APIs and SaaS services that your agents need to call. See [Registering Tools](../platform/registering-tools.md).
- **Deploy your own agent** -- Upload your own code instead of the sample. The analysis engine supports Python agents with LangChain, LangGraph, CrewAI, and more.
- **Set up identity providers** -- Configure JWT-based authentication so your client applications can call agents with user identity. See [Identity Providers](../platform/identity-providers.md).
- **Configure approvals** -- Mark sensitive tools as requiring approval to enable just-in-time access control. See [Approvals](../platform/approvals.md).

!!! tip "Want to use the API or CLI instead?"

    You can do everything shown above programmatically.

    - [:octicons-arrow-right-24: API Quickstart](api-quickstart.md) -- Deploy agents with curl or your favorite HTTP client
    - [:octicons-arrow-right-24: CLI Quickstart](cli-quickstart.md) -- Manage RunAgents from the terminal
