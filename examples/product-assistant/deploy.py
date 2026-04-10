"""
deploy.py — One-shot deploy script for the product-assistant agent.

This script:
  1. Reads credentials from env vars or ~/.runagents/config.json
  2. Registers the three tools on the platform (idempotent — safe to re-run)
  3. Deploys the agent with tool + model bindings
  4. Polls until the agent is Running
  5. Prints the invoke URL

Usage:
    python deploy.py

Prerequisites:
    pip install runagents

    # Set credentials (one of):
    runagents config set endpoint https://<your-id>.try.runagents.io
    runagents config set api-key  ra_ws_YOUR_KEY_HERE
    # or:
    export RUNAGENTS_ENDPOINT=https://<your-id>.try.runagents.io
    export RUNAGENTS_API_KEY=ra_ws_YOUR_KEY_HERE
"""

import sys
import time

from runagents import Client
from runagents.config import load_config

# ---------------------------------------------------------------------------
# Tool definitions
#
# base_url: the root URL of your actual API
#           Replace these with your real endpoints before deploying.
#
# For local testing with mock_tools/server.py:
#   base_url = "http://localhost:9090"   ← only works for local dev, not cloud
#
# For cloud deploy, you need a publicly reachable URL, e.g.:
#   base_url = "https://api.your-company.com"
#
# The platform creates an Istio ServiceEntry for each External tool,
# routing all agent traffic through the mesh where auth is injected.
# ---------------------------------------------------------------------------

TOOLS_TO_REGISTER = [
    {
        "name": "product-catalog",
        # ↓ Replace with your real product catalog API URL
        "base_url": "https://api.your-company.com",
        "description": "Product catalog — look up products by ID. GET /products/{id}",
        "auth_type": "None",   # "None" | "APIKey" | "OAuth2"
        "port": 443,
        "scheme": "HTTPS",
    },
    {
        "name": "inventory-service",
        # ↓ Replace with your real inventory service URL
        "base_url": "https://api.your-company.com",
        "description": "Real-time inventory levels. GET /inventory/{sku}",
        "auth_type": "None",
        "port": 443,
        "scheme": "HTTPS",
    },
    {
        "name": "pricing-engine",
        # ↓ Replace with your real pricing engine URL
        "base_url": "https://api.your-company.com",
        "description": "Pricing with volume discounts. POST /pricing/quote",
        "auth_type": "None",
        "port": 443,
        "scheme": "HTTPS",
    },
]

# ---------------------------------------------------------------------------
# Agent configuration
# ---------------------------------------------------------------------------

AGENT_NAME = "product-assistant"
AGENT_FILE = "agent.py"
NAMESPACE = "default"  # your workspace namespace

SYSTEM_PROMPT = (
    "You are a helpful product assistant for an e-commerce store. "
    "You have access to get_product, check_inventory, and get_pricing_quote tools. "
    "Always check inventory before quoting prices. "
    "For quantities over 50, volume discounts apply — always call get_pricing_quote."
)

LLM_CONFIGS = [
    {
        "provider": "openai",     # openai | anthropic | bedrock | ollama
        "model": "gpt-4o-mini",   # any model your provider supports
        "role": "default",
    }
]


# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------


def main():
    cfg = load_config()
    print(f"Deploying to: {cfg.endpoint}")
    print(f"Namespace:    {cfg.namespace or NAMESPACE}")
    print()

    client = Client()

    # --- Step 1: Register tools ---
    print("Registering tools...")
    for tool in TOOLS_TO_REGISTER:
        try:
            result = client.tools.create(
                name=tool["name"],
                base_url=tool["base_url"],
                description=tool["description"],
                auth_type=tool["auth_type"],
                port=tool["port"],
                scheme=tool["scheme"],
            )
            if isinstance(result, dict) and result.get("error"):
                # Tool likely already exists — that's fine
                print(f"  {tool['name']}: already exists (skipping)")
            else:
                print(f"  {tool['name']}: registered ✓")
        except Exception as e:
            if "already exists" in str(e).lower() or "conflict" in str(e).lower():
                print(f"  {tool['name']}: already exists (skipping)")
            else:
                print(f"  {tool['name']}: ERROR — {e}", file=sys.stderr)
                sys.exit(1)

    print()

    # --- Step 2: Read agent source code ---
    try:
        with open(AGENT_FILE) as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: {AGENT_FILE} not found. Run this script from the product-assistant/ directory.", file=sys.stderr)
        sys.exit(1)

    # --- Step 3: Deploy agent ---
    print(f"Deploying agent '{AGENT_NAME}'...")
    try:
        result = client.agents.deploy(
            name=AGENT_NAME,
            source_files={AGENT_FILE: source_code},
            system_prompt=SYSTEM_PROMPT,
            required_tools=[t["name"] for t in TOOLS_TO_REGISTER],
            llm_configs=LLM_CONFIGS,
            entry_point=AGENT_FILE,
            requirements="runagents>=1.3.1\n",
        )
        print(f"  Deploy request accepted ✓")
        if hasattr(result, "tools_created") and result.tools_created:
            print(f"  Tools created: {result.tools_created}")
    except Exception as e:
        print(f"Deploy failed: {e}", file=sys.stderr)
        sys.exit(1)

    print()

    # --- Step 4: Poll for Running status ---
    print("Waiting for agent to be Running", end="", flush=True)
    deadline = time.time() + 120  # 2-minute timeout
    ns = cfg.namespace or NAMESPACE

    while time.time() < deadline:
        try:
            agent_info = client.agents.get(ns, AGENT_NAME)
            status = agent_info.status
            if status == "Running":
                print(f" ✓")
                break
            elif status == "Failed":
                print(f"\nAgent failed to start. Check logs in the console.")
                sys.exit(1)
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(5)
    else:
        print(f"\nTimeout waiting for Running status. Check the console for build logs.")
        sys.exit(1)

    # --- Done ---
    endpoint = cfg.endpoint.rstrip("/")
    invoke_url = f"{endpoint}/api/agents/{ns}/{AGENT_NAME}/invoke"

    print()
    print("=" * 60)
    print(f"Agent deployed: {AGENT_NAME}")
    print(f"Invoke URL:     {invoke_url}")
    print()
    print("Test it:")
    print(f'  curl -X POST {invoke_url} \\')
    print(f'    -H "Authorization: Bearer {cfg.api_key or "YOUR_API_KEY"}" \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"message": "What products do you have?"}}\' ')
    print("=" * 60)


if __name__ == "__main__":
    main()
