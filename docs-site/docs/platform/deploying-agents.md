# Deploying Agents

RunAgents deploys your AI agent from source code in three steps: **Upload**, **Wire**, and **Deploy**. The platform analyzes your code, detects external dependencies (tool calls, LLM usage, secrets), and lets you map them to registered platform resources before going live.

Navigate to **Agents** in the sidebar, then click **+ New Agent** to open the deploy wizard.

---

## Step 1: Upload

Upload your agent's source code files. The platform accepts Python, TypeScript, JavaScript, and other common languages.

You have two options:

- **Drag and drop** your source files (or click to browse)
- **Try a Sample** -- loads the built-in Hello World agent, which uses the platform's starter echo tool and playground model provider

!!! info "What happens during analysis"
    After uploading, the platform automatically analyzes your code and detects:

    - **Tool calls** -- outbound HTTP requests to external APIs (e.g., Stripe, GitHub, Slack)
    - **LLM usage** -- calls to language model APIs (OpenAI, Anthropic, Bedrock, etc.) with model names and roles
    - **Secrets** -- hardcoded API keys or credentials that should be moved to secure storage
    - **Outbound destinations** -- all external hosts your agent communicates with
    - **Required packages** -- pip requirements, npm dependencies, etc.
    - **Entry point** -- the main file to run

Analysis takes a few seconds. You will see a progress indicator as it moves through parsing, detection, scanning, and enrichment phases. Once complete, you advance to the Wire step automatically.

---

## Step 2: Wire for Production

The Wire step presents everything the analysis found and lets you map each detected dependency to a registered platform resource.

### Tools

Each detected tool call is shown as a card with:

- The detected tool name and base URL from your code
- A dropdown to select a **registered tool** on the platform
- A **Register new** link if the tool does not exist yet (opens the tool registration form in a new tab)

When you select a matching tool, the card shows a green checkmark. All detected tools must be wired before you can deploy.

!!! tip "Register tools inline"
    Click **Register new** to open the tool registration page in a new tab. When you return to the deploy wizard, the tool list refreshes automatically -- no need to reload.

### Models

Each detected LLM usage is shown as a card with:

- The detected provider, model name, and role (e.g., `chat`, `embedding`)
- A dropdown to select a **registered model provider**
- A model selector for choosing the specific model from that provider

### Access Control

Optionally configure how clients authenticate to your agent:

- **Open** -- any client can call the agent (no authentication required)
- **Authenticated** -- requires a JWT from a registered identity provider. Select which identity provider to use.

### Agent Identity

Configure the agent's metadata:

| Field | Description |
|-------|-------------|
| **Agent name** | A unique identifier for this agent (required) |
| **System prompt** | Initial instructions for the agent's LLM context (auto-populated from analysis if detected) |

A **wiring progress bar** at the top of the page tracks how many items are fully wired. When all required items show green checkmarks and the agent name is set, the **Deploy** button becomes active.

---

## Step 3: Deploy

The final step shows a **deployment summary** with all your configuration choices:

- Agent name
- Source image (built from source or a custom pre-built image)
- System prompt
- Wired tools and model providers
- Identity provider (if configured)
- Access mode

Review the summary, then click **Deploy Now**.

The platform:

1. Builds a container image from your source code (if not using a custom image)
2. Creates the agent with all configured tool bindings and model provider mappings
3. Starts the agent

A progress animation shows the build and deploy phases. When deployment succeeds, you see a **success screen** with:

- A summary of what was deployed
- **View Agent** -- navigates to the agent detail page
- **Deploy Another** -- starts a fresh deploy wizard

!!! warning "Build pipeline"
    If the build service is not configured on your platform instance, you can still deploy by providing a pre-built container image. Toggle **Use custom image** in the Wire step and enter your image URL.

---

## Hello World Quick Start

The fastest way to deploy your first agent is the **Hello World** flow:

1. From the Dashboard, click **Deploy Hello World Agent** (or go to **Agents > + New Agent** and click **Try a Sample**)
2. The platform seeds the starter kit (echo tool + playground model provider) and loads sample code
3. Analysis runs automatically -- all tools and models are pre-wired with green checkmarks
4. Agent name is pre-filled as `hello-world`
5. Review the wiring and click **Deploy**

The sample agent does two things:

```python
# 1. Calls the built-in echo tool
echo_result = call_echo_tool("Hello from my first agent!")

# 2. Asks the LLM a question via the gateway
answer = ask_llm("Summarize what RunAgents does in one sentence.")
```

No external API keys or accounts are needed.

---

## Agent Detail Page

After deployment, navigate to **Agents** and click on an agent to view its detail page. The detail page has two tabs:

### Overview Tab

Shows the agent's current configuration:

- **Status** -- current phase (Pending, Running, or Failed)
- **System prompt** -- the configured system prompt
- **Wired tools** -- list of tools the agent has access to
- **Model configuration** -- the LLM provider and model being used
- **Identity provider** -- if authentication is configured

### Runs Tab

Lists all runs for this agent. Each run shows:

- Run ID and status
- User identity (who triggered the run)
- Timestamp
- Click a run to view the **Run Detail page** with a full event timeline and approval actions

---

## Agent Status Phases

| Phase | Meaning |
|-------|---------|
| **Pending** | Agent is being created; resources are being provisioned |
| **Running** | Agent is live and accepting requests |
| **Failed** | Agent failed to start; check the status message for details |

---

## What's Next

| Goal | Where to go |
|------|------------|
| Register a tool for your agent | [Registering Tools](registering-tools.md) |
| Configure an LLM provider | [Model Providers](model-providers.md) |
| Set up client authentication | [Identity Providers](identity-providers.md) |
| Understand the approval workflow | [Approvals](approvals.md) |
