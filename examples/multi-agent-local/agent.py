"""
Multi-agent customer support system — pure LangChain.

Three agents, each with a focused role:
  KnowledgeAgent  — answers questions from the FAQ / knowledge base
  AccountAgent    — handles account lookups and plan changes
  Coordinator     — classifies the request and routes to the right agent

Run locally:
    python agent.py "What is your return policy?"
    python agent.py "Look up account CUST-001"

Deploy to RunAgents (no changes to this file):
    runagents deploy --name support-agent --files agent.py,tools.py,requirements.txt ...

The RunAgents runtime discovers the module-level `chain` variable and
calls chain.invoke({"input": message}) automatically. Identity, policy,
and credential injection are handled by the platform — nothing here changes.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda

from tools import search_faq, lookup_account, update_account_plan, create_support_ticket

llm = ChatOpenAI(model=os.environ.get("LLM_MODEL", "gpt-4o-mini"), temperature=0)

MAX_ITER = 6


def run_agent(system_prompt: str, tools: list, message: str) -> str:
    """Run a single LLM agent with a tool-calling loop."""
    lm = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=message)]

    for _ in range(MAX_ITER):
        response = lm.invoke(messages)
        messages.append(response)

        if not getattr(response, "tool_calls", None):
            return response.content or ""

        for tc in response.tool_calls:
            fn = tool_map.get(tc["name"])
            result = fn.invoke(tc["args"]) if fn else f"Unknown tool: {tc['name']}"
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return "Reached maximum steps without a final answer."


# --- Specialist agents ---

def knowledge_agent(question: str) -> str:
    return run_agent(
        "You are a knowledge base specialist. Answer questions about company "
        "policies, products, shipping, returns, and procedures. "
        "Search the FAQ to find accurate answers. Be concise.",
        tools=[search_faq],
        message=question,
    )


def account_agent(question: str) -> str:
    return run_agent(
        "You are an account management specialist. Help with account lookups, "
        "billing questions, and subscription plan changes. "
        "Always look up the account before making changes. "
        "Create a support ticket for issues you cannot resolve directly.",
        tools=[lookup_account, update_account_plan, create_support_ticket],
        message=question,
    )


# --- Coordinator: routes to the right specialist ---

@tool
def route_to_knowledge_agent(question: str) -> str:
    """Route to the knowledge agent for FAQ, policy, and product questions."""
    return knowledge_agent(question)


@tool
def route_to_account_agent(question: str) -> str:
    """Route to the account agent for account lookups, billing, and plan changes."""
    return account_agent(question)


def coordinator(message: str) -> str:
    return run_agent(
        "You are a customer support coordinator. Route the request to the right specialist:\n"
        "  route_to_knowledge_agent — policies, products, FAQ, how-to questions\n"
        "  route_to_account_agent   — account info, billing, plan changes\n"
        "Always route to a specialist. Use their response as your final answer.",
        tools=[route_to_knowledge_agent, route_to_account_agent],
        message=message,
    )


# ---------------------------------------------------------------------------
# chain — the RunAgents runtime discovers this variable automatically.
# It calls chain.invoke({"input": message}) on each request.
# No handler function, no RunAgents imports needed.
# ---------------------------------------------------------------------------
chain = RunnableLambda(lambda x: coordinator(x["input"]))


# --- Local entry point ---

if __name__ == "__main__":
    import sys

    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY to run locally."); sys.exit(1)

    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is your return policy?"
    print(f"User: {message}\n" + "-" * 60)
    print(f"Agent: {chain.invoke({'input': message})}")
