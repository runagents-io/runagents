"""LangGraph-based expense review workflow for the RunAgents catalog."""

from __future__ import annotations

import json
import os
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from runagents import Agent


SYSTEM_PROMPT = """You are a finance review agent operating as a reasoning workflow.

Decide what evidence is needed before writing the review packet. Use the
available tools to gather ERP policy context and expense submission details.
Avoid redundant calls.

When you answer, produce a finance review packet with these sections:
1. Expense Summary
2. Policy Signals
3. Exceptions And Risks
4. Recommendation
5. Approval Notes

Do not approve expenses on your own. If the evidence suggests an exception,
route it to human review explicitly.
"""

FINALIZE_PROMPT = """You are finalizing an expense review after the workflow hit its tool budget.

Do not ask for more tools. Produce the best possible review packet from the
available evidence and call out any approval uncertainty.
"""

MAX_TOOL_ROUNDS = 3


class ExpenseState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    objective: str
    review_prompt: str
    context: dict[str, list[str]]
    evidence: list[str]
    rounds: int


TOOL_SPECS = {
    "erp": {
        "context_key": "policy_context",
        "purpose": "expense policy thresholds, reimbursable rules, and approver requirements",
        "preferred_fields": ("policy", "title", "summary"),
    },
    "expense-system": {
        "context_key": "submission_context",
        "purpose": "expense line items, merchant details, attendees, and receipts",
        "preferred_fields": ("merchant", "title", "summary"),
    },
}


tool_client = Agent()
llm = ChatOpenAI(model=os.environ.get("LLM_MODEL", "gpt-4.1"), temperature=0.0)


def _message_text(message: Any) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts)
    return str(content or "")


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return cleaned


def _stringify_item(item: Any, preferred_fields: tuple[str, ...]) -> str:
    if isinstance(item, str):
        return item.strip()
    if not isinstance(item, dict):
        return str(item).strip()

    primary = ""
    for field in preferred_fields:
        value = item.get(field)
        if value is not None and str(value).strip():
            primary = str(value).strip()
            break

    details: list[str] = []
    for field in ("amount", "currency", "status", "policy", "owner", "reason"):
        value = item.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if not text or text == primary:
            continue
        details.append(f"{field.replace('_', ' ')}: {text}")

    if primary and details:
        return f"{primary} ({'; '.join(details[:3])})"
    if primary:
        return primary
    if details:
        return "; ".join(details[:3])
    return ""


def _coerce_items(value: Any, preferred_fields: tuple[str, ...]) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = [_stringify_item(item, preferred_fields) for item in value[:8]]
        return [item for item in items if item]
    text = _stringify_item(value, preferred_fields)
    return [text] if text else []


def _parse_request(user_prompt: str) -> tuple[str, dict[str, list[str]]]:
    cleaned = _strip_code_fence(user_prompt)
    objective = cleaned or "Prepare an expense review packet."
    context = {
        "policy_context": [],
        "submission_context": [],
    }

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return objective, context

    if not isinstance(payload, dict):
        return objective, context

    objective = str(payload.get("objective") or payload.get("message") or objective).strip() or objective
    context["policy_context"] = _coerce_items(payload.get("policy_context"), ("policy", "title", "summary"))
    context["submission_context"] = _coerce_items(payload.get("expense_report") or payload.get("submission_context"), ("merchant", "title", "summary"))
    return objective, context


def _normalize_tool_items(raw: Any, preferred_fields: tuple[str, ...]) -> list[str]:
    if isinstance(raw, dict):
        for key in ("items", "results", "records", "data", "policies", "expenses", "reports"):
            if key in raw:
                items = _coerce_items(raw.get(key), preferred_fields)
                if items:
                    return items
        return _coerce_items(raw, preferred_fields)
    return _coerce_items(raw, preferred_fields)


def _section_lines(title: str, items: list[str], empty_message: str) -> list[str]:
    lines = [title]
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append(f"- {empty_message}")
    lines.append("")
    return lines


def _build_prompt(objective: str, context: dict[str, list[str]], evidence: list[str]) -> str:
    prompt_lines = [f"Objective: {objective}", ""]
    prompt_lines.extend(_section_lines("Policy context:", context.get("policy_context", []), "No ERP or policy context available."))
    prompt_lines.extend(_section_lines("Submission context:", context.get("submission_context", []), "No expense submission context available."))
    prompt_lines.extend(_section_lines("Evidence trail:", evidence, "No evidence trail captured."))
    return "\n".join(prompt_lines)


def _call_managed_tool(tool_name: str, objective: str) -> str:
    spec = TOOL_SPECS[tool_name]
    try:
        response = tool_client.call_tool(
            tool_name,
            payload={
                "objective": objective,
                "purpose": spec["purpose"],
                "audience": "expense-review",
                "limit": 6,
            },
        )
        items = _normalize_tool_items(response, spec["preferred_fields"])
        note = f"Retrieved {len(items)} item(s) from {tool_name}." if items else f"{tool_name} responded but returned no reusable finance review items."
    except Exception as exc:
        items = []
        note = f"{tool_name} retrieval unavailable: {exc}"

    return json.dumps({
        "tool": tool_name,
        "context_key": spec["context_key"],
        "items": items,
        "note": note,
    })


@tool("erp", description="Retrieve reimbursement policy, limits, and approver requirements.")
def erp_tool(objective: str) -> str:
    return _call_managed_tool("erp", objective)


@tool("expense-system", description="Retrieve expense submission details, line items, and receipt context.")
def expense_system_tool(objective: str) -> str:
    return _call_managed_tool("expense-system", objective)


EXPENSE_TOOLS = [erp_tool, expense_system_tool]
TOOL_NODE = ToolNode(EXPENSE_TOOLS)
AGENT_LLM = llm.bind_tools(EXPENSE_TOOLS)


def ingest_request(state: ExpenseState) -> dict[str, Any]:
    message = _message_text(state.get("messages", [])[-1]) if state.get("messages") else ""
    objective, context = _parse_request(message)

    evidence = [f"Expense review objective: {objective}"]
    for tool_name, spec in TOOL_SPECS.items():
        items = context.get(spec["context_key"], [])
        if items:
            evidence.append(f"Used {len(items)} {tool_name} signal(s) supplied in the request payload.")

    return {
        "objective": objective,
        "context": context,
        "evidence": evidence,
        "review_prompt": _build_prompt(objective, context, evidence),
        "rounds": 0,
    }


def reasoning_agent(state: ExpenseState) -> dict[str, Any]:
    objective = state.get("objective", "Prepare an expense review packet.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    prompt = state.get("review_prompt") or _build_prompt(objective, context, evidence)
    history = [message for message in state.get("messages", []) if isinstance(message, (AIMessage, ToolMessage))]

    response = AGENT_LLM.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
        *history,
    ])
    return {"messages": [response], "rounds": state.get("rounds", 0) + 1}


def route_after_agent(state: ExpenseState) -> str:
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        if state.get("rounds", 0) >= MAX_TOOL_ROUNDS:
            return "finalize_review"
        return "tool_node"
    return END


def integrate_tool_outputs(state: ExpenseState) -> dict[str, Any]:
    context = dict(state.get("context", {}))
    evidence = list(state.get("evidence", []))

    for message in state.get("messages", []):
        if not isinstance(message, ToolMessage):
            continue
        try:
            payload = json.loads(_message_text(message))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        context_key = str(payload.get("context_key", "")).strip()
        items = payload.get("items")
        note = str(payload.get("note", "")).strip()
        if context_key and isinstance(items, list):
            context[context_key] = [str(item).strip() for item in items if str(item).strip()]
        if note:
            evidence.append(note)

    return {
        "context": context,
        "evidence": evidence,
        "review_prompt": _build_prompt(
            state.get("objective", "Prepare an expense review packet."),
            context,
            evidence,
        ),
    }


def finalize_review(state: ExpenseState) -> dict[str, Any]:
    objective = state.get("objective", "Prepare an expense review packet.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    prompt = state.get("review_prompt") or _build_prompt(objective, context, evidence)
    response = llm.invoke([
        SystemMessage(content=FINALIZE_PROMPT),
        HumanMessage(content=prompt),
    ])
    return {"messages": [response]}


builder = StateGraph(ExpenseState)
builder.add_node("ingest_request", ingest_request)
builder.add_node("reasoning_agent", reasoning_agent)
builder.add_node("tool_node", TOOL_NODE)
builder.add_node("integrate_tool_outputs", integrate_tool_outputs)
builder.add_node("finalize_review", finalize_review)

builder.add_edge(START, "ingest_request")
builder.add_edge("ingest_request", "reasoning_agent")
builder.add_conditional_edges(
    "reasoning_agent",
    route_after_agent,
    {
        "tool_node": "tool_node",
        "finalize_review": "finalize_review",
        END: END,
    },
)
builder.add_edge("tool_node", "integrate_tool_outputs")
builder.add_edge("integrate_tool_outputs", "reasoning_agent")
builder.add_edge("finalize_review", END)

graph = builder.compile()
