"""
agent.py — Enterprise HR Assistant built with LangChain.

Uses RunAgents for:
  - Identity propagation   (X-End-User-ID header end-to-end)
  - Policy enforcement     (Open / Restricted / requireApproval per tool)
  - JIT approvals          (ApprovalRequired exception → pause + resume)
  - LLM Gateway routing    (OPENAI_BASE_URL auto-set by platform)
  - Credential injection   (API keys and OAuth2 tokens injected by mesh)

The agent uses LangChain's tool-calling pattern via bind_tools + LCEL.
All platform security features operate at the HTTP/mesh layer —
transparent to LangChain.

Deployment:
    runagents deploy --name hr-assistant --files agent.py,tools.py,requirements.txt ...
    # or:
    python deploy.py
"""

import json
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools import ALL_TOOLS, set_user_context
from runagents.runtime import ApprovalRequired

# ---------------------------------------------------------------------------
# LLM — ChatOpenAI reads OPENAI_BASE_URL automatically.
#
# LOCAL:    set OPENAI_API_KEY in your env; ChatOpenAI calls OpenAI directly.
# PLATFORM: the runtime injects OPENAI_BASE_URL (LLM Gateway) and
#           OPENAI_API_KEY before this file loads. ChatOpenAI routes
#           through the gateway automatically — nothing to configure here.
# ---------------------------------------------------------------------------
llm = ChatOpenAI(
    model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    temperature=0,
)

# Bind tools so the LLM knows what functions it can call
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Tool name → callable map for dispatch
TOOL_MAP = {t.name: t for t in ALL_TOOLS}

# ---------------------------------------------------------------------------
# System prompt — injected from Agent CRD spec.systemPrompt at runtime.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    """You are an HR assistant for a corporation. You help HR analysts with:
- Company policies and procedures (search_knowledge_base — always available)
- Employee information (get_employee — requires employee-directory access)
- Compensation changes (update_compensation — requires admin approval each time)

Always verify the employee exists before making compensation changes.
When a compensation change requires approval, explain what was submitted
and provide the action ID for tracking.

Compensation changes are logged with the requester's identity for audit purposes."""
)

MAX_ITERATIONS = int(os.environ.get("MAX_TOOL_ITERATIONS", "8"))


# ---------------------------------------------------------------------------
# Tool-calling loop
#
# We implement the loop manually (instead of using AgentExecutor) so we
# can catch ApprovalRequired at exactly the right moment and return a
# structured paused-approval response.
# ---------------------------------------------------------------------------

def run_tool_loop(messages: list) -> dict:
    """
    Run LangChain tool-calling loop until done or approval required.

    Returns:
        {"response": str}                         — completed normally
        {"response": str, "approval_required": …} — paused for approval
    """
    for _ in range(MAX_ITERATIONS):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # No tool calls — final answer
        if not getattr(response, "tool_calls", None):
            return {"response": response.content or ""}

        # Execute each tool call
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_id   = tc["id"]

            fn = TOOL_MAP.get(tool_name)
            if fn is None:
                tool_result = f"Unknown tool: {tool_name}"
            else:
                try:
                    tool_result = fn.invoke(tool_args)
                except ApprovalRequired as e:
                    # ---------------------------------------------------
                    # A tool call hit requireApproval: true in its
                    # PolicyBinding. The mesh created an AccessRequest
                    # and returned 403 APPROVAL_REQUIRED.
                    #
                    # tools.py caught the 403 and raised ApprovalRequired.
                    # We propagate it to the handler via _approval_required_response().
                    #
                    # What the platform runtime does at this point
                    # (BEFORE this line executes):
                    #   1. Saves full conversation checkpoint to governance
                    #      (messages + pending tool calls)
                    #   2. Moves the run to PAUSED_APPROVAL
                    #
                    # The checkpoint is stored in governance — NOT in this pod.
                    # This means: even if this pod crashes, is restarted, or
                    # is replaced with a new version before the admin approves,
                    # the resume will still work. The ResumeWorker fetches
                    # the checkpoint from governance and calls /resume/<action_id>
                    # on whatever pod is running at that point.
                    #
                    # Your handler is NOT called on resume.
                    # The runtime handles resume entirely:
                    #   3. Admin approves: runagents approvals approve <action_id>
                    #   4. ResumeWorker fetches checkpoint from governance
                    #   5. Calls POST /resume/<action_id> on this pod
                    #   6. Runtime re-executes the blocked tool call (now allowed)
                    #   7. Continues the LLM loop and returns the final response
                    # ---------------------------------------------------
                    return _approval_required_response(e)

            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))

    return {"response": "Reached maximum iterations without a final answer."}


def _approval_required_response(e: ApprovalRequired) -> dict:
    detail    = e.detail or {}
    action_id = detail.get("action_id", "")
    run_id    = detail.get("run_id", "")
    tool_name = detail.get("tool", e.tool_name or "unknown")

    user_msg = (
        f"This action requires admin approval before it can proceed.\n\n"
        f"An access request has been submitted for **{tool_name}**. "
        f"An HR administrator will review it shortly.\n\n"
        f"Action ID: `{action_id}`\n"
        f"Run ID: `{run_id}`\n\n"
        f"You'll be notified when the action is approved and completed. "
        f"To check status: `runagents approvals list`"
    )
    return {
        "response":          user_msg,
        "approval_required": detail,
        "status":            "PAUSED_APPROVAL",
    }


# ---------------------------------------------------------------------------
# Handler function — called by the RunAgents runtime on each /invoke request.
#
# IDENTITY FLOW:
#   The platform extracts the user's verified identity from the JWT at
#   the ingress and injects it as X-End-User-ID. The runtime passes it
#   as request["user_id"]. We store it in a ContextVar (tools.py) so
#   every tool call includes it in outbound requests, making user identity
#   visible in tool server logs end-to-end.
#
# APPROVAL FLOW:
#   If a tool hits a requireApproval PolicyBinding, run_tool_loop() above
#   returns a paused response. The platform runtime saves a checkpoint.
#   The ResumeWorker resumes via /resume/<action_id> automatically.
# ---------------------------------------------------------------------------

def handler(request: dict, ctx) -> dict:
    """
    Handle an incoming agent request.

    Args:
        request: {
            "message": str,        # user's message
            "history": list[dict], # prior turns
            "user_id": str,        # X-End-User-ID from JWT (verified identity)
        }
        ctx: RunContext — provides ctx.tools, ctx.llm_url, ctx.model

    Returns:
        str | dict — string response or dict with "response" key.
        Approval-paused responses include "approval_required" and "status" keys.
    """
    message = request.get("message", "")
    history = request.get("history", [])
    user_id = request.get("user_id", "")

    # Propagate verified identity to all tool calls in this request.
    # tools.py reads this ContextVar to set X-End-User-ID on every
    # outbound HTTP call. The mesh also forwards it automatically.
    if user_id:
        set_user_context(user_id)

    # Build message list: system prompt + conversation history + new message
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in history:
        role    = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=message))

    return run_tool_loop(messages)


# ---------------------------------------------------------------------------
# Local smoke test
# Run: python agent.py "What is the maternity leave policy?"
#      python agent.py "Look up employee EMP-001"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from types import SimpleNamespace

    os.environ.setdefault("TOOL_DEFINITIONS_JSON", "[]")
    os.environ.setdefault("TOOL_ROUTES_JSON", "{}")
    os.environ.setdefault("LLM_GATEWAY_URL", "http://localhost:8080/v1/chat/completions")

    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("RUNAGENTS_ENDPOINT")):
        print("Set OPENAI_API_KEY or RUNAGENTS_ENDPOINT to test locally.")
        sys.exit(1)

    if os.environ.get("OPENAI_API_KEY"):
        os.environ.pop("OPENAI_BASE_URL", None)  # use direct OpenAI

    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the PTO policy?"
    ctx     = SimpleNamespace(tools={}, llm_url="", model="gpt-4o-mini", system_prompt=SYSTEM_PROMPT)

    print(f"User (as developer@local): {message}")
    print("-" * 60)

    result = handler({"message": message, "history": [], "user_id": "developer@local"}, ctx)
    if isinstance(result, dict):
        print(f"Agent: {result.get('response', result)}")
        if result.get("approval_required"):
            print(f"\n[Paused — approval required]")
            print(f"Action ID: {result['approval_required'].get('action_id', 'act-local-test')}")
            print("Run: runagents approvals approve <action-id>")
    else:
        print(f"Agent: {result}")
