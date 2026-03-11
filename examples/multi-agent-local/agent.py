"""
agent.py — Multi-agent customer support system built with LangChain.

Three agents, each with a focused role:

  KnowledgeAgent  — answers questions using the FAQ / knowledge base
  AccountAgent    — handles account lookups and plan changes
  Coordinator     — classifies the request and routes to the right agent

This file runs identically in both environments:

  LOCAL:     python agent.py "your question"
             Tools call mock_server.py on localhost

  PLATFORM:  runagents deploy (or python deploy.py)
             Same code. The platform adds:
               - Identity: X-End-User-ID from JWT flows to every tool call
               - Policy:   each tool's access is checked by ext-authz
               - Credentials: API keys / OAuth2 tokens injected by the mesh
               - Resume:  if a tool requires approval, the run pauses and
                          resumes automatically — your code here is unchanged

No conditional logic, no platform-specific imports, no if/else for env.
The difference between local and deployed is purely infrastructure.
"""

import os
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool as lc_tool

from tools import (
    search_faq,
    lookup_account,
    update_account_plan,
    create_support_ticket,
    set_user_id,
)

# ---------------------------------------------------------------------------
# LLM
#
# LOCAL:    set OPENAI_API_KEY in your env; ChatOpenAI calls OpenAI directly.
# PLATFORM: the runtime injects OPENAI_BASE_URL (LLM Gateway) and
#           OPENAI_API_KEY before this file loads. ChatOpenAI routes
#           through the gateway automatically — nothing to configure here.
# ---------------------------------------------------------------------------
llm = ChatOpenAI(model=os.environ.get("LLM_MODEL", "gpt-4o-mini"), temperature=0)

MAX_ITER = 6  # max tool-calling iterations per agent


# ---------------------------------------------------------------------------
# Agent runner — shared tool-calling loop for all agents
# ---------------------------------------------------------------------------

def run_agent(system_prompt: str, tools: list, user_message: str) -> str:
    """Run a single agent with a tool-calling loop. Returns final text response."""
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    for _ in range(MAX_ITER):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not getattr(response, "tool_calls", None):
            return response.content or ""

        for tc in response.tool_calls:
            fn   = tool_map.get(tc["name"])
            result = fn.invoke(tc["args"]) if fn else f"Unknown tool: {tc['name']}"
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return "Reached maximum steps without a final answer."


# ---------------------------------------------------------------------------
# Agent 1: KnowledgeAgent
# Answers questions about policies, products, and procedures.
# Tools: search_faq
# ---------------------------------------------------------------------------

def knowledge_agent(question: str) -> str:
    return run_agent(
        system_prompt=(
            "You are a knowledge base specialist. Answer questions about company "
            "policies, products, shipping, returns, and procedures. "
            "Search the FAQ to find accurate answers. Be concise."
        ),
        tools=[search_faq],
        user_message=question,
    )


# ---------------------------------------------------------------------------
# Agent 2: AccountAgent
# Handles account lookups, billing questions, and plan changes.
# Tools: lookup_account, update_account_plan, create_support_ticket
# ---------------------------------------------------------------------------

def account_agent(request: str) -> str:
    return run_agent(
        system_prompt=(
            "You are an account management specialist. Help customers with account "
            "lookups, billing questions, and subscription plan changes. "
            "Always look up the account first before making changes. "
            "Create a support ticket for issues you cannot resolve directly."
        ),
        tools=[lookup_account, update_account_plan, create_support_ticket],
        user_message=request,
    )


# ---------------------------------------------------------------------------
# Coordinator
#
# Classifies the request and routes to the right agent.
# The coordinator itself does not call external tools — it calls the
# specialist agents above as functions.
# ---------------------------------------------------------------------------

# Expose agents as LangChain tools so the coordinator can call them
@lc_tool
def route_to_knowledge_agent(question: str) -> str:
    """Route to the knowledge agent for FAQ, policy, and product questions."""
    return knowledge_agent(question)


@lc_tool
def route_to_account_agent(request: str) -> str:
    """Route to the account agent for account lookups, billing, and plan changes."""
    return account_agent(request)


def coordinator(message: str) -> str:
    return run_agent(
        system_prompt=(
            "You are a customer support coordinator. Classify the customer's request "
            "and route it to the right specialist:\n\n"
            "  route_to_knowledge_agent — policies, products, FAQ, how-to questions\n"
            "  route_to_account_agent  — account info, billing, plan changes\n\n"
            "Use the specialist's response as your final answer. "
            "Do not answer from your own knowledge — always route to a specialist."
        ),
        tools=[route_to_knowledge_agent, route_to_account_agent],
        user_message=message,
    )


# ---------------------------------------------------------------------------
# Handler — entry point for the RunAgents platform runtime
#
# The runtime discovers `handler(request, ctx)` and calls it on each
# POST /invoke request.
#
# request["user_id"] is the X-End-User-ID header value — the user's
# verified identity extracted from the JWT at the platform ingress.
# We pass it to tools.py so every outbound tool call carries the identity.
# ---------------------------------------------------------------------------

def handler(request: dict, ctx) -> str:
    message = request.get("message", "")
    user_id = request.get("user_id", "")

    # Propagate verified identity to all tool calls.
    # On the platform the mesh also forwards X-End-User-ID automatically —
    # setting it here makes it visible locally too.
    if user_id:
        set_user_id(user_id)

    return coordinator(message)


# ---------------------------------------------------------------------------
# Local entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY to run locally.")
        print("  export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is your return policy?"
    print(f"User: {message}")
    print("-" * 60)

    from types import SimpleNamespace
    result = handler({"message": message, "user_id": "local-dev"}, SimpleNamespace())
    print(f"Agent: {result}")
