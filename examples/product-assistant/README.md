# Product Assistant — End-to-End RunAgents Example

A fully working AI agent that helps users look up products, check inventory,
and get pricing quotes. Covers the complete RunAgents workflow:

```
[You] → Register Tools → Deploy Agent → Invoke → Monitor Runs
```

---

## What This Example Covers

| Step | What Happens |
|------|-------------|
| 1. Credentials | Get your workspace URL + API key |
| 2. Register Tools | Tell the platform about your APIs |
| 3. Deploy Agent | Upload agent code + wire tool/LLM bindings |
| 4. Invoke | Call the agent with a user message |
| 5. Monitor | Watch run events, tool calls, LLM responses |
| 6. Approvals | (Optional) Restrict pricing tool to require approval |

---

## Prerequisites

```bash
pip install runagents          # SDK + CLI
```

Verify:
```bash
runagents --help
python -c "from runagents import Client, Agent; print('OK')"
```

---

## Step 1: Get Your Credentials

### Option A — RunAgents Cloud (try.runagents.io)

1. Sign up at **https://try.runagents.io**
2. Log in to your workspace console
3. Click your workspace name in the top-left → **Settings → API Keys**
4. Copy your **API Key** (starts with `ra_ws_...`) and **Workspace URL**
   - URL format: `https://<your-id>.try.runagents.io`

### Option B — Self-Hosted

Use the URL and any API key you configured for your deployment.

### Configure the CLI

```bash
runagents config set endpoint https://<your-id>.try.runagents.io
runagents config set api-key  ra_ws_YOUR_KEY_HERE
runagents config set namespace default
```

Verify connection:
```bash
runagents agents list    # should return [] on a fresh workspace
```

### Option C — Environment Variables (CI/CD)

```bash
export RUNAGENTS_ENDPOINT=https://<your-id>.try.runagents.io
export RUNAGENTS_API_KEY=ra_ws_YOUR_KEY_HERE
export RUNAGENTS_NAMESPACE=default
```

---

## Step 2: Start the Mock Tool Server (Local Testing)

This repo includes a local mock server that simulates your real APIs.
In production you would point tools at your actual API endpoints.

```bash
python mock_tools/server.py
```

Output:
```
Mock tool server running on http://localhost:9090
  GET  /products/{id}       → product details
  GET  /inventory/{sku}     → stock levels
  POST /pricing/quote       → calculate price with discounts
  GET  /healthz             → health check
```

Keep this running in a separate terminal while you test locally.

---

## Step 3: Register the Tools on the Platform

Tools tell RunAgents how to reach your APIs and what auth they require.
The platform then injects credentials and enforces policies at egress.

### Via CLI

```bash
# Product catalog — read-only, no auth needed for this example
runagents tools create \
  --name product-catalog \
  --base-url https://your-api.example.com \
  --description "Product catalog — look up products by ID" \
  --auth-type None

# Inventory service — read-only
runagents tools create \
  --name inventory-service \
  --base-url https://your-api.example.com \
  --description "Real-time inventory levels by SKU" \
  --auth-type None

# Pricing engine — mutating, can require approval for high-value quotes
runagents tools create \
  --name pricing-engine \
  --base-url https://your-api.example.com \
  --description "Calculate pricing with volume discounts and promotions" \
  --auth-type None
```

> **Tip:** For tools at your actual API: replace `https://your-api.example.com`
> with the real base URL. The platform will route all calls through that
> hostname via the Istio mesh.

### Via Python (deploy.py handles this automatically)

See `deploy.py` — it registers all three tools and the agent in one script.

### Verify

```bash
runagents tools list
```

---

## Step 4: Seed a Model Provider

If your workspace doesn't already have a model provider (LLM), seed one:

```bash
runagents starter-kit     # creates echo-tool + playground-llm (gpt-4o-mini)
```

Or register your own:

```bash
# You need an OpenAI API key for this
runagents models create \
  --name openai-gpt4o \
  --provider openai \
  --model gpt-4o-mini \
  --api-key sk-YOUR_OPENAI_KEY
```

> The agent code never sees your OpenAI key — the platform stores it in a
> K8s Secret and injects it at runtime. You just call the LLM Gateway URL.

---

## Step 5: Deploy the Agent

### Quick deploy via CLI

```bash
runagents deploy \
  --name product-assistant \
  --file agent.py \
  --tool product-catalog \
  --tool inventory-service \
  --tool pricing-engine \
  --model openai/gpt-4o-mini
```

### Programmatic deploy (recommended for CI/CD)

```bash
python deploy.py
```

This script:
1. Registers all three tools (idempotent — safe to re-run)
2. Deploys the agent with correct tool + model bindings
3. Prints the agent URL for invoking

### Verify deployment

```bash
runagents agents list
runagents agents get default product-assistant
```

Wait for `status: Running` (usually ~30 seconds for the first deploy).

---

## Step 6: Invoke the Agent

### Via curl

```bash
# Replace with your workspace URL
curl -X POST https://<your-id>.try.runagents.io/api/agents/default/product-assistant/invoke \
  -H "Authorization: Bearer ra_ws_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message": "Do you have the wireless headphones in stock? And what is the price for 10 units?"}'
```

### Via Python

```python
import urllib.request, json

endpoint = "https://<your-id>.try.runagents.io"
api_key  = "ra_ws_YOUR_KEY_HERE"

req = urllib.request.Request(
    f"{endpoint}/api/agents/default/product-assistant/invoke",
    data=json.dumps({"message": "What products do you have?"}).encode(),
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    print(json.loads(resp.read())["response"])
```

### Via the Console

1. Open your workspace console
2. Navigate to **Agents → product-assistant**
3. Click **Playground** tab
4. Type a message and watch the tool call cards animate in real time

### Streaming (SSE)

```bash
curl -X POST https://<your-id>.try.runagents.io/api/agents/default/product-assistant/invoke/stream \
  -H "Authorization: Bearer ra_ws_YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message": "Check inventory for SKU-001 and quote 5 units"}' \
  --no-buffer
```

You'll see events like:
```
data: {"type":"tool_call","tool":"product-catalog","input":{"product_id":"SKU-001"}}
data: {"type":"tool_result","tool":"product-catalog","output":{"name":"...","price":29.99}}
data: {"type":"content","delta":"Based on the inventory check..."}
data: {"type":"done"}
data: [DONE]
```

---

## Step 7: Monitor Runs

```bash
# List recent runs
runagents runs list --agent product-assistant

# Get full event timeline for a run
runagents runs get <run-id>
```

Or in Python:

```python
from runagents import Client

client = Client()
runs = client.runs.list(agent="product-assistant")
for run in runs[:3]:
    print(f"{run.id}  {run.status}")
    events = client.runs.events(run.id)
    for event in events:
        print(f"  [{event.type}] {event.data}")
```

---

## Step 8: (Optional) Require Approval for Pricing Quotes

High-value pricing quotes may need human sign-off before the agent can
execute them. To enable this:

1. Create or update a policy bound to the agent with a matching `approval_required` rule for pricing write operations.
2. Add approver groups in policy `spec.approvals` for who can approve.

Now when the agent tries to call the pricing engine:
- The run **pauses** with status `PAUSED_APPROVAL`
- An access request appears in **Approvals** in the console (or via CLI)
- An admin approves it
- The agent **automatically resumes** from where it paused

```bash
# See pending approvals
runagents approvals list

# Approve one
runagents approvals approve <request-id>
```

---

## Local Development

To run and test the agent entirely locally (no platform needed):

```bash
# Terminal 1: mock tool server
python mock_tools/server.py

# Terminal 2: agent dev server
runagents dev

# Terminal 3: test it
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the price for 5 units of PRD-001?"}'
```

`runagents dev` reads `runagents.yaml`, starts the runtime on `:8080`,
and points all tool URLs at the local mock server on `:9090`.

---

## Project Structure

```
product-assistant/
├── README.md             # This file
├── agent.py              # Agent handler (Tier 2 — custom handler function)
├── runagents.yaml        # Agent config (tools, model, system prompt)
├── requirements.txt      # Python dependencies
├── deploy.py             # One-shot deploy script (tools + agent)
├── invoke.py             # Example invocation + monitoring script
├── mock_tools/
│   ├── server.py         # Local mock API server (stdlib only)
│   └── data.py           # Fake product/inventory data
└── .env.example          # Environment variable template
```

---

## Troubleshooting

**Agent status is `Failed`**
```bash
runagents agents get default product-assistant   # check status.message
```
Usually means the container image failed to build. Check the build logs
in the console under **Agents → product-assistant → Logs**.

**Tool calls return 403**
The agent ServiceAccount is missing a matching allow/approval policy binding,
or a deny rule took precedence. Check bound policies and capability matches.

**"Connection refused" on local dev**
Make sure `python mock_tools/server.py` is running before `runagents dev`.

**`runagents: command not found`**
```bash
pip install runagents
# or if using system Python:
python -m runagents.cli.main --help
```
