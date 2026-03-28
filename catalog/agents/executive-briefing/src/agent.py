"""LangGraph-based executive briefing blueprint for RunAgents catalog."""

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


SYSTEM_PROMPT = """You are an executive briefing assistant.
Produce a concise leadership brief with these sections:
1. Executive Summary
2. Today's Critical Meetings
3. Risks And Decisions
4. Stakeholder Signals
5. Recommended Next Step

Separate facts from recommendations. If context is missing, say so plainly.
"""


class BriefingState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    objective: str
    context: dict[str, list[str]]
    evidence: list[str]


TOOL_SPECS = {
    "calendar": {
        "context_key": "meetings",
        "purpose": "todays leadership meetings and checkpoints",
        "preferred_fields": ("title", "subject", "name"),
    },
    "project-tracker": {
        "context_key": "project_updates",
        "purpose": "active delivery risks, blockers, and pending executive decisions",
        "preferred_fields": ("title", "summary", "name"),
    },
    "knowledge-base": {
        "context_key": "reference_notes",
        "purpose": "reference notes, docs, and background context relevant to the briefing",
        "preferred_fields": ("title", "summary", "text"),
    },
    "chat": {
        "context_key": "stakeholder_notes",
        "purpose": "stakeholder sentiment, escalations, and notable follow-up signals",
        "preferred_fields": ("signal", "summary", "text", "name"),
    },
}


tool_client = Agent()
llm = ChatOpenAI(model=os.environ.get("LLM_MODEL", "gpt-4.1"), temperature=0.1)


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
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(part for part in parts if part)
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
    for field in ("status", "decision", "owner", "signal", "summary", "next_step"):
        value = item.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if not text or text == primary:
            continue
        label = field.replace("_", " ")
        details.append(f"{label}: {text}")

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
        items = [_stringify_item(item, preferred_fields) for item in value[:6]]
        return [item for item in items if item]
    text = _stringify_item(value, preferred_fields)
    return [text] if text else []


def _parse_request(user_prompt: str) -> tuple[str, dict[str, list[str]]]:
    cleaned = _strip_code_fence(user_prompt)
    objective = cleaned or "Prepare today's executive briefing."
    context = {
        "meetings": [],
        "project_updates": [],
        "reference_notes": [],
        "stakeholder_notes": [],
    }

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return objective, context

    if not isinstance(payload, dict):
        return objective, context

    objective = str(payload.get("objective") or payload.get("message") or objective).strip() or objective
    context["meetings"] = _coerce_items(payload.get("meetings"), ("title", "subject", "name"))
    context["project_updates"] = _coerce_items(payload.get("project_updates"), ("title", "summary", "name"))
    context["reference_notes"] = _coerce_items(payload.get("reference_notes"), ("title", "summary", "text"))
    context["stakeholder_notes"] = _coerce_items(payload.get("stakeholder_notes"), ("signal", "summary", "text", "name"))
    return objective, context


def _normalize_tool_items(raw: Any, preferred_fields: tuple[str, ...]) -> list[str]:
    if isinstance(raw, dict):
        for key in ("items", "results", "records", "data", "meetings", "updates", "notes", "messages", "documents"):
            if key in raw:
                items = _coerce_items(raw.get(key), preferred_fields)
                if items:
                    return items
        return _coerce_items(raw, preferred_fields)
    return _coerce_items(raw, preferred_fields)


def _call_managed_tool(tool_name: str, objective: str) -> str:
    spec = TOOL_SPECS[tool_name]
    try:
        response = tool_client.call_tool(
            tool_name,
            payload={
                "objective": objective,
                "purpose": spec["purpose"],
                "audience": "executive-briefing",
                "limit": 5,
            },
        )
        items = _normalize_tool_items(response, spec["preferred_fields"])
        if items:
            note = f"Retrieved {len(items)} item(s) from {tool_name}."
        else:
            note = f"{tool_name} responded but returned no reusable briefing items."
    except Exception as exc:
        items = []
        note = f"{tool_name} retrieval unavailable: {exc}"

    return json.dumps({
        "tool": tool_name,
        "context_key": spec["context_key"],
        "items": items,
        "note": note,
    })


@tool("calendar", description="Retrieve today's leadership meetings and checkpoints.")
def calendar_tool(objective: str) -> str:
    return _call_managed_tool("calendar", objective)


@tool("project-tracker", description="Retrieve active delivery risks, blockers, and pending decisions.")
def project_tracker_tool(objective: str) -> str:
    return _call_managed_tool("project-tracker", objective)


@tool("knowledge-base", description="Retrieve reference notes and background context for the briefing.")
def knowledge_base_tool(objective: str) -> str:
    return _call_managed_tool("knowledge-base", objective)


@tool("chat", description="Retrieve stakeholder sentiment, escalations, and notable follow-up signals.")
def chat_signals_tool(objective: str) -> str:
    return _call_managed_tool("chat", objective)


BRIEFING_TOOLS = [
    calendar_tool,
    project_tracker_tool,
    knowledge_base_tool,
    chat_signals_tool,
]
TOOL_NODE = ToolNode(BRIEFING_TOOLS)


def ingest_request(state: BriefingState) -> dict[str, Any]:
    message = ""
    if state.get("messages"):
        message = _message_text(state["messages"][-1])
    objective, context = _parse_request(message)

    evidence = [f"Briefing objective: {objective}"]
    for tool_name, spec in TOOL_SPECS.items():
        items = context.get(spec["context_key"], [])
        if items:
            evidence.append(f"Used {len(items)} {tool_name} signal(s) supplied in the request payload.")

    return {
        "objective": objective,
        "context": context,
        "evidence": evidence,
    }


def plan_retrieval(state: BriefingState) -> dict[str, Any]:
    context = state.get("context", {})
    objective = state.get("objective", "Prepare today's executive briefing.")
    tool_calls = []

    for tool_name, spec in TOOL_SPECS.items():
        if context.get(spec["context_key"], []):
            continue
        tool_calls.append({
            "name": tool_name,
            "args": {"objective": objective},
            "id": f"{tool_name}-briefing",
            "type": "tool_call",
        })

    if not tool_calls:
        return {}

    return {
        "messages": [
            AIMessage(
                content="Collect the missing context needed for the executive briefing.",
                tool_calls=tool_calls,
            )
        ]
    }


def route_after_plan(state: BriefingState) -> str:
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        return "tool_node"
    return "synthesize_brief"


def integrate_tool_outputs(state: BriefingState) -> dict[str, Any]:
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

    return {"context": context, "evidence": evidence}


def _section_lines(title: str, items: list[str], empty_message: str) -> list[str]:
    lines = [title]
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append(f"- {empty_message}")
    lines.append("")
    return lines


def synthesize_brief(state: BriefingState) -> dict[str, Any]:
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    objective = state.get("objective", "Prepare today's executive briefing.")

    prompt_lines = [f"Objective: {objective}", ""]
    prompt_lines.extend(
        _section_lines("Meetings:", context.get("meetings", []), "No meetings were provided or retrieved.")
    )
    prompt_lines.extend(
        _section_lines(
            "Project updates:",
            context.get("project_updates", []),
            "No project updates were provided or retrieved.",
        )
    )
    prompt_lines.extend(
        _section_lines(
            "Reference notes:",
            context.get("reference_notes", []),
            "No reference notes were provided or retrieved.",
        )
    )
    prompt_lines.extend(
        _section_lines(
            "Stakeholder signals:",
            context.get("stakeholder_notes", []),
            "No stakeholder signals were provided or retrieved.",
        )
    )
    prompt_lines.extend(_section_lines("Evidence trail:", evidence, "No evidence trail captured."))
    prompt = "\n".join(prompt_lines)

    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )
    return {"messages": [response]}


builder = StateGraph(BriefingState)
builder.add_node("ingest_request", ingest_request)
builder.add_node("plan_retrieval", plan_retrieval)
builder.add_node("tool_node", TOOL_NODE)
builder.add_node("integrate_tool_outputs", integrate_tool_outputs)
builder.add_node("synthesize_brief", synthesize_brief)

builder.add_edge(START, "ingest_request")
builder.add_edge("ingest_request", "plan_retrieval")
builder.add_conditional_edges(
    "plan_retrieval",
    route_after_plan,
    {
        "tool_node": "tool_node",
        "synthesize_brief": "synthesize_brief",
    },
)
builder.add_edge("tool_node", "integrate_tool_outputs")
builder.add_edge("integrate_tool_outputs", "synthesize_brief")
builder.add_edge("synthesize_brief", END)

graph = builder.compile()
