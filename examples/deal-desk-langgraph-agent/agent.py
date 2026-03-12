"""Deal Desk demo agent (LangGraph).

This is designed for enterprise demo flows:
1) low-risk CRM updates (auto-allow)
2) high-risk ERP credit notes (approval-gated by policy)

The runtime discovers `graph` and invokes it for each `/invoke` request.
"""

import json
import os
from typing import Annotated, Any, TypedDict

import requests
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOpenAI(
    model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    temperature=0,
)

CRM_TOOL_URL = os.environ.get(
    "TOOL_URL_CRM_UPDATE_OPPORTUNITY",
    "http://crm-update-opportunity.agent-system.svc:8080",
)
ERP_TOOL_URL = os.environ.get(
    "TOOL_URL_ERP_ISSUE_CREDIT_NOTE",
    "http://erp-issue-credit-note.agent-system.svc:8080",
)
REQUEST_TIMEOUT_SECS = float(os.environ.get("TOOL_REQUEST_TIMEOUT_SECS", "15"))

SYSTEM_PROMPT = os.environ.get(
    "SYSTEM_PROMPT",
    (
        "You are a Deal Desk assistant.\n"
        "- Use crm_update_opportunity for opportunity stage/progress updates.\n"
        "- Use erp_issue_credit_note for credit/refund actions.\n"
        "- Do not fabricate missing fields. Ask follow-up questions when needed.\n"
        "- For ERP credit note, require invoice_id, customer_id, amount_usd, and reason.\n"
        "- Keep final user responses concise and action-oriented."
    ),
)

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "crm_update_opportunity",
            "description": "Update CRM opportunity stage/details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "opportunity_id": {"type": "string"},
                    "stage": {
                        "type": "string",
                        "enum": [
                            "qualified",
                            "proposal",
                            "negotiation",
                            "closed_won",
                            "closed_lost",
                        ],
                    },
                    "amount_usd": {"type": "number"},
                    "next_step": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["opportunity_id", "stage"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "erp_issue_credit_note",
            "description": "Issue an ERP credit note for an invoice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "string"},
                    "customer_id": {"type": "string"},
                    "amount_usd": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["invoice_id", "customer_id", "amount_usd", "reason"],
            },
        },
    },
]

llm_with_tools = llm.bind_tools(tools_schema)


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECS)
    except requests.RequestException as exc:
        return {"ok": False, "error": f"request_failed: {exc}"}

    if resp.status_code >= 400:
        return {"ok": False, "error": f"http_{resp.status_code}", "body": resp.text[:500]}

    try:
        data = resp.json()
    except ValueError:
        data = {"raw": resp.text}

    if isinstance(data, dict):
        return {"ok": True, **data}
    return {"ok": True, "data": data}


def _crm_update_opportunity(args: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "opportunity_id": args.get("opportunity_id"),
        "stage": args.get("stage"),
        "amount_usd": args.get("amount_usd"),
        "next_step": args.get("next_step"),
        "note": args.get("note"),
    }
    return _post_json(f"{CRM_TOOL_URL}/crm/opportunity/update", payload)


def _erp_issue_credit_note(args: dict[str, Any]) -> dict[str, Any]:
    amount = args.get("amount_usd")
    if amount is not None:
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {"ok": False, "error": "invalid_amount_usd"}

    payload = {
        "invoice_id": args.get("invoice_id"),
        "customer_id": args.get("customer_id"),
        "amount_usd": amount,
        "reason": args.get("reason"),
    }
    return _post_json(f"{ERP_TOOL_URL}/erp/credit-note/issue", payload)


TOOL_DISPATCH = {
    "crm_update_opportunity": _crm_update_opportunity,
    "erp_issue_credit_note": _erp_issue_credit_note,
}


def call_model(state: AgentState) -> AgentState:
    model_input = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = llm_with_tools.invoke(model_input)
    return {"messages": [response]}


def call_tools(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    results = []
    for tc in getattr(last, "tool_calls", []) or []:
        tool_name = tc.get("name", "")
        tool_args = tc.get("args", {}) or {}
        handler = TOOL_DISPATCH.get(tool_name)
        if handler is None:
            content = {"ok": False, "error": f"unknown_tool:{tool_name}"}
        else:
            content = handler(tool_args)
        results.append(ToolMessage(content=json.dumps(content), tool_call_id=tc["id"]))
    return {"messages": results}


def should_call_tools(state: AgentState) -> str:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "end"


workflow = StateGraph(AgentState)
workflow.add_node("model", call_model)
workflow.add_node("tools", call_tools)

workflow.add_edge(START, "model")
workflow.add_conditional_edges("model", should_call_tools, {"tools": "tools", "end": END})
workflow.add_edge("tools", "model")

graph = workflow.compile()
