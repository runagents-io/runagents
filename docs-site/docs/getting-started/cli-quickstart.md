---
title: CLI Quickstart
description: Manage RunAgents from your terminal — install the CLI, deploy agents, and monitor runs.
---

# CLI Quickstart

The RunAgents CLI lets you manage agents, tools, model providers, and runs from your terminal. This guide walks through installation, configuration, and deploying your first agent.

!!! info "Prerequisites"

    You need a RunAgents account and an API key. If you do not have an account yet, email [try@runagents.io](mailto:try@runagents.io) to request trial access.

---

## Step 1: Install the CLI

=== "curl (macOS / Linux)"

    ```bash
    curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
    ```

=== "npm"

    ```bash
    npm install -g @runagents/cli
    ```

=== "Binary Download"

    Download for your platform from [releases.runagents.io](https://runagents-releases.s3.amazonaws.com/cli/v1.0.0/) and add it to your `PATH`.

Verify the installation:

```bash
runagents version
```

```
runagents v0.8.0 (build 2026-02-20)
```

---

## Step 2: Configure the CLI

Point the CLI at your RunAgents instance and provide your API key.

```bash
runagents config set endpoint https://api.runagents.io
runagents config set api-key ra_live_abc123your-api-key-here
```

Verify the connection:

```bash
runagents config view
```

```
Endpoint:  https://api.runagents.io
API Key:   ra_live_abc1...  (set)
Project:   default
```

!!! tip

    The CLI stores configuration in `~/.runagents/config.yaml`. You can also set `RUNAGENTS_ENDPOINT` and `RUNAGENTS_API_KEY` as environment variables.

---

## Step 3: Seed Starter Resources

Create the built-in Echo Tool and Playground LLM so you have something to wire your first agent to.

```bash
runagents starter-kit
```

```
 Created tool: echo-tool
 Created model provider: playground-llm

Starter resources are ready. You can now deploy an agent.
```

This is idempotent -- running it again has no effect if the resources already exist.

---

## Step 4: Deploy an Agent

Create a file called `agent.py` with the following content:

```python
import urllib.request
import json
import os

def main():
    tool_url = os.environ.get("TOOL_ECHO_TOOL_URL")
    llm_url = os.environ.get("LLM_GATEWAY_URL")

    # Call the echo tool
    req = urllib.request.Request(
        f"{tool_url}/echo",
        data=json.dumps({"message": "Hello from my agent!"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print(f"Echo says: {result}")

    # Call the LLM
    llm_req = urllib.request.Request(
        f"{llm_url}/v1/chat/completions",
        data=json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": result["echo"]}],
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    llm_resp = urllib.request.urlopen(llm_req)
    print(json.loads(llm_resp.read()))

if __name__ == "__main__":
    main()
```

Now deploy it:

```bash
runagents deploy \
  --name hello-world \
  --file agent.py \
  --tool echo-tool \
  --model openai/gpt-4o-mini
```

```
Analyzing agent.py...
  Detected tools:     echo-tool
  Detected LLM usage: gpt-4o-mini (default)
  Secrets found:      0
  Entry point:        agent.py

Deploying agent "hello-world"...
  Agent created:      hello-world
  Policies created:   hello-world-echo-tool-auto
  Status:             Pending

Agent deployed successfully. Run `runagents agents get hello-world` to check status.
```

The CLI analyzes the file, wires the detected tools and LLM usage, and deploys the agent in a single command.

### Deploy Flags

| Flag | Description | Example |
|---|---|---|
| `--name` | Agent name (required) | `--name hello-world` |
| `--file` | Source file to include (repeatable) | `--file agent.py --file utils.py` |
| `--tool` | Existing tool to require (repeatable) | `--tool echo-tool --tool slack-api` |
| `--model` | LLM config as `provider/model` | `--model openai/gpt-4o-mini` |
| `--model-role` | Role for the preceding `--model` | `--model-role planner` |
| `--identity-provider` | Identity provider name | `--identity-provider auth0-prod` |

---

## Step 5: List Agents

```bash
runagents agents list
```

```
NAME           STATUS    TOOLS        MODEL           AGE
hello-world    Running   echo-tool    gpt-4o-mini     2m
```

Get detailed information about a specific agent:

```bash
runagents agents get hello-world
```

```
Name:             hello-world
Status:           Running
Created:          2026-02-23T10:15:30Z

Required Tools:
  - echo-tool (Open access, auto-bound)

LLM Configuration:
  - Role: default | Provider: openai | Model: gpt-4o-mini

Policies:
  - hello-world-echo-tool-auto (Allow)
```

---

## Step 6: View Runs

List all runs for the hello-world agent:

```bash
runagents runs list --agent hello-world
```

```
ID              STATE       STARTED                  DURATION
run-7f2a9c3e    COMPLETED   2026-02-23T10:16:45Z     2.1s
run-a1b2c3d4    RUNNING     2026-02-23T10:20:12Z     --
```

---

## Step 7: Check Run Details

Get the full timeline of a specific run:

```bash
runagents runs get run-7f2a9c3e
```

```
Run ID:       run-7f2a9c3e
Agent:        hello-world
State:        COMPLETED
Started:      2026-02-23T10:16:45Z
Completed:    2026-02-23T10:16:47Z
Duration:     2.1s

Events:
  #1  10:16:45  RUN_STARTED        Agent invoked
  #2  10:16:45  TOOL_CALL          POST echo-tool/echo -> 200 (0.3s)
  #3  10:16:46  LLM_CALL           gpt-4o-mini -> 200 (1.5s)
  #4  10:16:47  RUN_COMPLETED      Success
```

If a run is paused waiting for approval, you will see:

```bash
runagents runs get run-x9y8z7w6
```

```
Run ID:       run-x9y8z7w6
Agent:        data-agent
State:        PAUSED_APPROVAL
Started:      2026-02-23T11:05:00Z

Events:
  #1  11:05:00  RUN_STARTED        Agent invoked
  #2  11:05:01  TOOL_CALL          POST sensitive-api/data -> 403 (0.1s)
  #3  11:05:01  APPROVAL_REQUIRED  Waiting for admin approval (action-abc123)

Blocked Actions:
  ID              TOOL            STATUS     CREATED
  action-abc123   sensitive-api   PENDING    2026-02-23T11:05:01Z
```

---

## Other Useful Commands

### List registered tools

```bash
runagents tools list
```

```
NAME          TYPE       ACCESS    AUTH
echo-tool     Internal   Open      None
```

### List model providers

```bash
runagents models list
```

```
NAME              PROVIDER    MODELS          STATUS
playground-llm    openai      gpt-4o-mini     Available
```

### View access requests

```bash
runagents approvals list
```

```
ID                  TOOL            AGENT          STATUS     CREATED
req-abc123          sensitive-api   data-agent     PENDING    2026-02-23T11:05:01Z
```

### Approve an access request

```bash
runagents approvals approve req-abc123
```

```
 Access request req-abc123 approved.
  Policy created: data-agent-sensitive-api-jit
  Expires: 2026-02-23T12:05:01Z (1h TTL)
```

---

## Next Steps

- [**CLI Commands Reference**](../cli/commands.md) -- Full list of all CLI commands and flags
- [**API Reference**](../api/overview.md) -- REST API documentation
- [**Registering Tools**](../platform/registering-tools.md) -- Add external APIs and SaaS services
- [**Policy Model**](../concepts/policy-model.md) -- Understand access control and auto-binding
- [**Approvals**](../platform/approvals.md) -- Configure just-in-time approval workflows

!!! tip "Need help?"

    Email [try@runagents.io](mailto:try@runagents.io) and we will get you set up.
