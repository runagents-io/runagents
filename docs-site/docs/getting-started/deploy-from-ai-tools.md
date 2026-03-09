---
title: Deploy from AI Coding Tools
description: Ship agents built with Claude Code, Codex, Cursor, or any AI coding tool to production with identity, policy, and approvals.
---

# Deploy from AI Coding Tools

You built an AI agent with Claude Code, OpenAI Codex, Cursor, or another AI coding tool. It works on your machine. Now deploy it to production with identity propagation, access control, and approval workflows -- in under 5 minutes.

---

## What Changes When You Go to Production

| What | Local | Production (RunAgents) |
|------|-------|------------------------|
| **API keys** | Your personal keys hardcoded or in `.env` | Per-user OAuth tokens injected automatically by the platform |
| **Access control** | None -- agent can call anything | Policy-driven, per-tool capability checks on every request |
| **Audit trail** | None | Every tool call logged with user identity, agent, timestamp |
| **Trust model** | You trust yourself | Approval workflows gate high-risk actions before they execute |

!!! tip "No code changes required"

    You do not need to rewrite your agent. The platform analyzes your code, detects what it calls, and handles the rest through infrastructure -- not code modifications.

---

## Step 1: Export Your Agent Code

Get your agent code into a `.py` file. Here is a realistic example -- an agent that looks up a customer in Stripe and sends a summary to Slack:

```python
"""Support agent -- looks up Stripe customers and posts to Slack."""
import os
import json
import openai
import requests

client = openai.OpenAI()
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

STRIPE_URL = os.environ.get("TOOL_URL_STRIPE", "https://api.stripe.com")
SLACK_URL = os.environ.get("TOOL_URL_SLACK", "https://slack.com/api")


def handler(request, context):
    message = request["message"]

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": context.system_prompt},
            {"role": "user", "content": message},
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "lookup_customer",
                    "description": "Look up a Stripe customer by email",
                    "parameters": {
                        "type": "object",
                        "properties": {"email": {"type": "string"}},
                        "required": ["email"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_slack_message",
                    "description": "Send a message to a Slack channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "text": {"type": "string"},
                        },
                        "required": ["channel", "text"],
                    },
                },
            },
        ],
    )

    choice = response.choices[0]
    if choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            args = json.loads(tc.function.arguments)
            if tc.function.name == "lookup_customer":
                resp = requests.get(
                    f"{STRIPE_URL}/v1/customers/search",
                    params={"query": f"email:'{args['email']}'"},
                )
                return {"response": f"Customer found: {resp.json()}"}
            elif tc.function.name == "send_slack_message":
                requests.post(
                    f"{SLACK_URL}/chat.postMessage",
                    json={"channel": args["channel"], "text": args["text"]},
                )
                return {"response": f"Message sent to {args['channel']}"}

    return {"response": choice.message.content}
```

Getting this file out of your AI coding tool:

=== "Claude Code"

    Your agent file is already in your project directory. Copy it or point the deploy wizard at it directly.

    ```bash
    # Your file is already on disk, e.g.:
    cp ~/projects/my-agent/agent.py .
    ```

=== "OpenAI Codex"

    Save the generated agent code to a `.py` file in your working directory.

    ```bash
    # Save from the Codex output to a file:
    # File > Save As > agent.py
    ```

=== "Cursor"

    Export the file from your Cursor workspace. It is already saved to your project directory.

    ```bash
    # Your file is in the workspace, e.g.:
    ls ~/projects/my-agent/agent.py
    ```

!!! note

    The platform supports any Python file that makes HTTP calls to external services. It does not matter which tool generated it. LangChain, LangGraph, CrewAI, raw `requests`, `httpx`, `urllib` -- all are detected automatically.

---

## Step 2: Sign Up at try.runagents.io

Go to [try.runagents.io](https://try.runagents.io) and enter your email address. You will receive a magic link -- click it, and your workspace is ready in about 60 seconds.

Your workspace comes with:

- A **console** for managing agents, tools, and models
- A **deploy wizard** that analyzes and deploys your code
- A **built-in playground** for testing agents interactively

!!! info "Already have an account?"

    Log in at your platform URL and skip to Step 3.

---

## Step 3: Upload to the Deploy Wizard

1. Open the console and navigate to **Agents** in the sidebar
2. Click **"+ New Agent"**
3. Drag and drop your `.py` file onto the upload area (or click to browse)

The platform analyzes your code automatically. Within seconds, the analysis results appear:

| Detected | Example |
|----------|---------|
| **Tool calls** | `requests.get("https://api.stripe.com/...")` -- Stripe API |
| **Tool calls** | `requests.post("https://slack.com/api/...")` -- Slack API |
| **Model usage** | `import openai` -- OpenAI SDK (gpt-4o-mini) |
| **Entry point** | `def handler(request, context)` -- custom handler function |

!!! tip

    If you have a `requirements.txt`, upload it alongside your agent file. The platform uses it to install the right pip packages in the container image.

---

## Step 4: Wire Tools and Models

The deploy wizard moves to the **Wire** step, where you connect detected tool calls and model usage to platform resources.

### Register tools

For each detected tool, you need a registered tool on the platform. Click **"Register new"** next to any unmatched tool to create one:

| Field | What to enter | Example |
|-------|---------------|---------|
| **Name** | A short identifier | `stripe` |
| **URL** | The tool's base URL | `https://api.stripe.com` |
| **Auth type** | How the tool authenticates | OAuth2, API Key, or None |
| **Access mode** | Who can call it | Open (auto-approved) or Approval Required |

=== "Open access"

    The agent gets immediate access. Good for low-risk tools like weather APIs or internal services.

=== "Approval required"

    Every call requires admin approval before it goes through. Use this for tools that modify data, charge money, or send messages.

### Map model providers

Select the model provider for your agent's LLM calls. If you do not have one registered yet, click **"Register new"** and enter:

- **Provider**: OpenAI, Anthropic, AWS Bedrock, or Ollama
- **Model**: The model name (e.g., `gpt-4o-mini`, `claude-sonnet-4-20250514`)
- **API key**: Stored securely as a platform secret

### Set the agent name

Give your agent a name (e.g., `support-agent`). This becomes its identity on the platform.

!!! warning

    If a tool or model shows a red indicator, it means the platform could not match it to a registered resource. Register the missing resource before proceeding.

---

## Step 5: Deploy

Click **Deploy**. The platform creates everything your agent needs:

| Resource | Purpose |
|----------|---------|
| **Agent** with service account | Identity for your agent in the platform |
| **Tool registrations** with networking rules | Secure, policy-checked routes to external APIs |
| **Policy bindings** | Access control rules linking your agent to its tools |
| **Configuration** | Tool URLs, LLM gateway endpoint, model settings -- all injected as environment variables |

The agent transitions from **Pending** to **Running** within a few seconds.

---

## Step 6: Test It

Once the agent is running, open the **Playground** tab on the agent detail page.

Type a message like:

> Look up the Stripe customer with email alice@example.com

Watch the platform in action:

1. Your message goes to the agent
2. The agent asks the LLM what to do
3. The LLM decides to call the `lookup_customer` tool
4. The platform intercepts the outbound call to Stripe:
    - Checks the access policy -- is this agent allowed to call Stripe?
    - Injects the correct authentication token for the end user
    - Forwards the request with the user's identity attached
5. The response flows back through the agent to you

The playground shows each step: tool calls with arguments, tool responses, and the final answer.

---

## What's Different Now

Here is what changed by deploying through RunAgents instead of running locally:

### Before (local)

```
You → Agent → Stripe (your API key, no checks, no logs)
```

### After (RunAgents)

```
User → Agent → Platform intercepts → Policy check → Token injection → Stripe
                                    ↓                                    ↓
                              Access denied?                     Audit logged
                              → Approval workflow triggered       with user identity
```

The key differences:

- **Identity flows end-to-end.** The `X-End-User-ID` header travels from the client through the agent to every tool call. Stripe sees which user initiated the request, not just which agent made it.

- **Every tool call is policy-checked.** The agent cannot call a tool it has not been granted access to. Capabilities are enforced at the method + path level -- an agent with read access to Stripe cannot create charges.

- **High-risk actions require approval.** If Slack is registered with "Approval Required," the agent pauses, an admin reviews the action, and only then does the message get sent.

- **Credentials are never in your code.** The platform injects OAuth tokens or API keys at the network layer. Your agent code has zero secrets.

---

---

## Advanced: Deploy Without Leaving Your AI Tool

For Claude Code, Codex, and Cursor users who want to stay in their editor, RunAgents supports an **action plan** workflow — your AI tool generates a structured JSON plan, you validate and apply it with the CLI.

### 1. Export workspace context

```bash
runagents config set endpoint https://your-workspace.try.runagents.io
runagents context export -o json > context.json
```

### 2. Ask your AI tool to generate a plan

=== "Claude Code"

    In Claude Code, paste `context.json` and say:

    ```
    Here is my RunAgents workspace context. I have an agent.py file that calls
    Stripe and Slack. Generate a RunAgents action plan JSON to register both tools
    and deploy the agent as "support-agent".
    ```

    Claude Code will produce a `plan.json` following the [Action Plan Schema](../cli/action-plans.md).

=== "OpenAI Codex"

    In your Codex prompt:

    ```
    Given this RunAgents context.json, create a plan.json to register
    a Stripe tool (https://api.stripe.com, OAuth2, Critical access) and
    deploy my agent.py as "support-agent" using gpt-4o-mini.
    ```

=== "Cursor"

    Open `context.json` in Cursor and use the chat panel:

    ```
    Use this RunAgents context to create a plan.json that wires
    my agent to its tools and deploys it.
    ```

### 3. Validate the plan

```bash
runagents action validate --file plan.json
```

```
Plan: bootstrap-support-agent
  ✓ tool.upsert         stripe            valid
  ✓ tool.upsert         slack             valid
  ✓ deploy.execute      support-agent     valid

All 3 actions valid.
```

### 4. Apply

```bash
runagents action apply --file plan.json
```

```
  ✓ tool.upsert     stripe         applied
  ✓ tool.upsert     slack          applied
  ✓ deploy.execute  support-agent  applied (Running)
```

!!! tip "Idempotent by design"
    Action plans use `idempotency_key` per action. Re-running the same plan is safe — already-applied actions are skipped.

See [External Assistants](../cli/external-assistants.md) and [Action Plans](../cli/action-plans.md) for the full schema and examples.

---

## Next Steps

| Goal | Guide |
|------|-------|
| Use the built-in terminal copilot | [Copilot](copilot.md) |
| Learn agent patterns in depth | [Writing Agents](writing-agents.md) |
| Register and configure external tools | [Registering Tools](../platform/registering-tools.md) |
| Understand the policy and access model | [Policy Model](../concepts/policy-model.md) |
| Set up approval workflows | [Approvals](../platform/approvals.md) |
| Configure identity providers for your users | [Identity Providers](../platform/identity-providers.md) |

!!! tip "Need help?"

    Reach out at [try@runagents.io](mailto:try@runagents.io) or open an issue on [GitHub](https://github.com/runagents-io/runagents).
