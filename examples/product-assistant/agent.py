"""
Product Assistant Agent
=======================

A Tier 2 agent with a custom handler function. Uses the RunAgents SDK to
call three platform tools: product-catalog, inventory-service, pricing-engine.

The operator injects these environment variables at runtime:
  SYSTEM_PROMPT          — from runagents.yaml or deploy --system-prompt
  LLM_GATEWAY_URL        — points to the platform's LLM gateway
  LLM_MODEL              — e.g. "gpt-4o-mini"
  TOOL_URL_PRODUCT_CATALOG   — base URL for product-catalog tool
  TOOL_URL_INVENTORY_SERVICE — base URL for inventory-service tool
  TOOL_URL_PRICING_ENGINE    — base URL for pricing-engine tool
  TOOL_DEFINITIONS_JSON  — OpenAI-format tool definitions (auto-generated)
  TOOL_ROUTES_JSON       — function → HTTP route map (auto-generated)

You never hard-code tool URLs or credentials here. The platform mesh
handles authentication, policy enforcement, and token injection.
"""

import json
import os
from runagents import Agent

# ---------------------------------------------------------------------------
# Initialise the agent — reads env vars injected by the operator
# ---------------------------------------------------------------------------

agent = Agent()

# ---------------------------------------------------------------------------
# Tool helper functions
# Tool URLs come from TOOL_URL_{NAME} env vars, injected at deploy time.
# Calls go through the Istio mesh — auth and policy are enforced automatically.
# ---------------------------------------------------------------------------


def get_product(product_id: str) -> dict:
    """Look up a product by ID from the product catalog."""
    return agent.call_tool(
        name="product-catalog",
        path=f"/products/{product_id}",
        method="GET",
    )


def check_inventory(sku: str) -> dict:
    """Get real-time stock levels for a SKU."""
    return agent.call_tool(
        name="inventory-service",
        path=f"/inventory/{sku}",
        method="GET",
    )


def get_pricing_quote(sku: str, quantity: int, promo_code: str = "") -> dict:
    """Calculate price for a given SKU and quantity, with optional promo code."""
    return agent.call_tool(
        name="pricing-engine",
        path="/pricing/quote",
        method="POST",
        payload={
            "sku": sku,
            "quantity": quantity,
            "promo_code": promo_code,
        },
    )


# ---------------------------------------------------------------------------
# Tool definitions for the LLM
# These tell the LLM what tools it can call and what parameters they take.
# In production these are auto-generated from your Tool CRD capabilities,
# but defining them here makes the agent work standalone in local dev too.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Look up a product by its ID. Returns name, description, SKU, base price, and category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID or SKU, e.g. 'PRD-001' or 'HEADPHONES-BT500'",
                    }
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check real-time stock levels for a product SKU. Returns quantity_available, warehouse_location, and restock_date if out of stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU to check inventory for",
                    }
                },
                "required": ["sku"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pricing_quote",
            "description": "Get a price quote for a quantity of a SKU. Applies volume discounts and promo codes automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU to price",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of units",
                    },
                    "promo_code": {
                        "type": "string",
                        "description": "Optional promotional code for additional discounts",
                    },
                },
                "required": ["sku", "quantity"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool dispatcher — maps LLM tool call names to Python functions
# ---------------------------------------------------------------------------

TOOL_DISPATCH = {
    "get_product": lambda args: get_product(args["product_id"]),
    "check_inventory": lambda args: check_inventory(args["sku"]),
    "get_pricing_quote": lambda args: get_pricing_quote(
        args["sku"], args["quantity"], args.get("promo_code", "")
    ),
}


# ---------------------------------------------------------------------------
# Agent handler — called by the platform runtime on each /invoke request
#
# Signature options (the runtime detects automatically):
#   def handler()                     — no args
#   def handler(request)              — receives {"message": ..., "history": [...]}
#   def handler(request, ctx)         — + RunContext with ctx.call_tool(), ctx.chat()
# ---------------------------------------------------------------------------


def handler(request: dict, ctx) -> str:
    """
    Handle a user request with a tool-calling loop.

    Args:
        request: {"message": str, "history": list[dict]}
        ctx:     RunContext — provides ctx.call_tool() and ctx.chat()

    Returns:
        Final response string from the LLM.
    """
    message = request["message"]
    history = request.get("history", [])

    # Build the message list: system prompt + prior history + new user message
    messages = [{"role": "system", "content": agent.system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    # --- Tool-calling loop ---
    # Ask the LLM, execute any tool calls it makes, feed results back.
    # Loop until the LLM produces a final text response (no more tool calls).

    max_iterations = int(os.environ.get("MAX_TOOL_ITERATIONS", "10"))

    for iteration in range(max_iterations):
        # Call the LLM through the gateway
        # LLM_GATEWAY_URL is injected by the operator — it's the platform's
        # OpenAI-compatible endpoint. Your OpenAI key never appears in this code.
        response = agent.chat(
            message="",          # message already in history
            tools=TOOLS,
            history=messages,    # pass full history so we don't repeat user msg
        )

        choice = response["choices"][0]
        finish_reason = choice["finish_reason"]
        assistant_msg = choice["message"]

        # Add the assistant's message to history
        messages.append(assistant_msg)

        # If the LLM made no tool calls, we have the final response
        if finish_reason != "tool_calls" or not assistant_msg.get("tool_calls"):
            return assistant_msg.get("content") or ""

        # Execute each tool call the LLM requested
        for tool_call in assistant_msg["tool_calls"]:
            fn_name = tool_call["function"]["name"]
            fn_args = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call["id"]

            # Dispatch to the right Python function
            if fn_name not in TOOL_DISPATCH:
                tool_result = {"error": f"Unknown tool: {fn_name}"}
            else:
                try:
                    tool_result = TOOL_DISPATCH[fn_name](fn_args)
                except Exception as exc:
                    # Surface errors to the LLM so it can reason about them
                    # (e.g. "item not found" or "insufficient stock")
                    tool_result = {"error": str(exc)}

            # Feed the tool result back to the LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": fn_name,
                "content": json.dumps(tool_result),
            })

    # Fallback if we hit max iterations (shouldn't happen in normal use)
    return "I wasn't able to complete that request. Please try rephrasing."


# ---------------------------------------------------------------------------
# Local test entry point
# Run directly for quick smoke tests: python agent.py
# For full local dev: runagents dev (starts the HTTP server automatically)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Minimal env setup for local testing without a platform
    os.environ.setdefault("SYSTEM_PROMPT", "You are a helpful product assistant.")
    os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")

    # When running locally, point at mock tool server (python mock_tools/server.py)
    os.environ.setdefault("TOOL_URL_PRODUCT_CATALOG", "http://localhost:9090")
    os.environ.setdefault("TOOL_URL_INVENTORY_SERVICE", "http://localhost:9090")
    os.environ.setdefault("TOOL_URL_PRICING_ENGINE", "http://localhost:9090")

    # LLM gateway: use OpenAI directly if OPENAI_API_KEY is set,
    # otherwise use the platform gateway
    if os.environ.get("OPENAI_API_KEY"):
        os.environ.setdefault(
            "LLM_GATEWAY_URL",
            "https://api.openai.com/v1/chat/completions",
        )
    elif os.environ.get("RUNAGENTS_ENDPOINT"):
        endpoint = os.environ["RUNAGENTS_ENDPOINT"].rstrip("/")
        os.environ.setdefault("LLM_GATEWAY_URL", f"{endpoint}/v1/chat/completions")
    else:
        print("Set OPENAI_API_KEY or RUNAGENTS_ENDPOINT to run locally.")
        sys.exit(1)

    # Re-init agent after env vars are set
    agent = Agent()

    test_messages = [
        "What wireless headphones do you have?",
        "Check if PRD-001 is in stock and give me a quote for 10 units",
        "Apply promo code SAVE20 to 5 units of PRD-002",
    ]

    msg = sys.argv[1] if len(sys.argv) > 1 else test_messages[0]
    print(f"\nUser: {msg}")
    print("-" * 60)

    # Simulate what the runtime does when it receives a /invoke request
    from types import SimpleNamespace
    ctx = SimpleNamespace(call_tool=agent.call_tool, chat=agent.chat)

    result = handler({"message": msg, "history": []}, ctx)
    print(f"Agent: {result}")
