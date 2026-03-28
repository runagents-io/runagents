"""LangGraph-based meeting follow-up workflow for the RunAgents catalog."""

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


SYSTEM_PROMPT = """You are a meeting follow-up agent operating as a reasoning workflow.

Decide what context is missing before writing the recap. Use the available tools
for meeting metadata, source notes, project tracker context, and stakeholder
signals. Avoid redundant tool calls.

When you answer, produce a clear follow-up with these sections:
1. Executive Summary
2. Decisions
3. Action Items
4. Draft Follow-Up Message
5. Open Questions

Only include grounded decisions and action items. If an owner or due date is not
available, say so explicitly instead of guessing.
"""

FINALIZE_PROMPT = """You are finalizing a meeting follow-up after the workflow hit its tool budget.

Do not ask for more tools. Produce the best possible follow-up using only the
currently available context.
"""

MAX_TOOL_ROUNDS = 4


class FollowUpState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    objective: str
    followup_prompt: str
    context: dict[str, list[str]]
    evidence: list[str]
    rounds: int


TOOL_SPECS = {
    "calendar": {
        "context_key": "meeting_context",
        "purpose": "meeting title, attendees, timing, and adjacent events",
        "preferred_fields": ("title", "subject", "name"),
    },
    "docs": {
        "context_key": "source_notes",
        "purpose": "meeting notes, transcript excerpts, and decisions captured in docs",
        "preferred_fields": ("title", "summary", "text"),
    },
    "project-tracker": {
        "context_key": "delivery_context",
        "purpose": "project tasks, owners, and dependencies affected by the meeting",
        "preferred_fields": ("title", "summary", "task"),
    },
    "chat": {
        "context_key": "stakeholder_signals",
        "purpose": "follow-up chatter, owner confirmations, and stakeholder concerns",
        "preferred_fields": ("signal", "summary", "text", "owner"),
    },
}


tool_client = Agent()
llm = ChatOpenAI(model=os.environ.get("LLM_MODEL", "gpt-4.1-mini"), temperature=0.1)


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
    for field in ("owner", "due", "status", "decision", "next_step"):
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
    objective = cleaned or "Prepare a meeting follow-up."
    context = {
        "meeting_context": [],
        "source_notes": [],
        "delivery_context": [],
        "stakeholder_signals": [],
    }

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return objective, context

    if not isinstance(payload, dict):
        return objective, context

    objective = str(payload.get("objective") or payload.get("message") or objective).strip() or objective
    context["meeting_context"] = _coerce_items(payload.get("meeting") or payload.get("meeting_context"), ("title", "subject", "name"))
    context["source_notes"] = _coerce_items(payload.get("notes") or payload.get("source_notes"), ("title", "summary", "text"))
    context["delivery_context"] = _coerce_items(payload.get("action_items") or payload.get("delivery_context"), ("task", "title", "summary"))
    context["stakeholder_signals"] = _coerce_items(payload.get("stakeholder_signals"), ("signal", "summary", "text", "owner"))
    return objective, context


def _normalize_tool_items(raw: Any, preferred_fields: tuple[str, ...]) -> list[str]:
    if isinstance(raw, dict):
        for key in ("items", "results", "records", "data", "notes", "tasks", "messages", "meetings"):
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
    prompt_lines.extend(_section_lines("Meeting context:", context.get("meeting_context", []), "No calendar context available."))
    prompt_lines.extend(_section_lines("Source notes:", context.get("source_notes", []), "No notes or transcript context available."))
    prompt_lines.extend(_section_lines("Delivery context:", context.get("delivery_context", []), "No project tracker context available."))
    prompt_lines.extend(_section_lines("Stakeholder signals:", context.get("stakeholder_signals", []), "No messaging or stakeholder context available."))
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
                "audience": "meeting-follow-up",
                "limit": 6,
            },
        )
        items = _normalize_tool_items(response, spec["preferred_fields"])
        note = f"Retrieved {len(items)} item(s) from {tool_name}." if items else f"{tool_name} responded but returned no reusable follow-up items."
    except Exception as exc:
        items = []
        note = f"{tool_name} retrieval unavailable: {exc}"

    return json.dumps({
        "tool": tool_name,
        "context_key": spec["context_key"],
        "items": items,
        "note": note,
    })


@tool("calendar", description="Retrieve meeting metadata, attendees, and scheduling context.")
def calendar_tool(objective: str) -> str:
    return _call_managed_tool("calendar", objective)


@tool("docs", description="Retrieve notes, transcript excerpts, and captured decisions from docs.")
def docs_tool(objective: str) -> str:
    return _call_managed_tool("docs", objective)


@tool("project-tracker", description="Retrieve related tasks, owners, and delivery dependencies.")
def project_tracker_tool(objective: str) -> str:
    return _call_managed_tool("project-tracker", objective)


@tool("chat", description="Retrieve owner confirmations and follow-up signals from team messaging.")
def chat_tool(objective: str) -> str:
    return _call_managed_tool("chat", objective)


FOLLOWUP_TOOLS = [calendar_tool, docs_tool, project_tracker_tool, chat_tool]
TOOL_NODE = ToolNode(FOLLOWUP_TOOLS)
AGENT_LLM = llm.bind_tools(FOLLOWUP_TOOLS)


def ingest_request(state: FollowUpState) -> dict[str, Any]:
    message = _message_text(state.get("messages", [])[-1]) if state.get("messages") else ""
    objective, context = _parse_request(message)

    evidence = [f"Follow-up objective: {objective}"]
    for tool_name, spec in TOOL_SPECS.items():
        items = context.get(spec["context_key"], [])
        if items:
            evidence.append(f"Used {len(items)} {tool_name} signal(s) supplied in the request payload.")

    return {
        "objective": objective,
        "context": context,
        "evidence": evidence,
        "followup_prompt": _build_prompt(objective, context, evidence),
        "rounds": 0,
    }


def reasoning_agent(state: FollowUpState) -> dict[str, Any]:
    objective = state.get("objective", "Prepare a meeting follow-up.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    prompt = state.get("followup_prompt") or _build_prompt(objective, context, evidence)
    history = [message for message in state.get("messages", []) if isinstance(message, (AIMessage, ToolMessage))]

    response = AGENT_LLM.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
        *history,
    ])
    return {"messages": [response], "rounds": state.get("rounds", 0) + 1}


def route_after_agent(state: FollowUpState) -> str:
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        if state.get("rounds", 0) >= MAX_TOOL_ROUNDS:
            return "finalize_followup"
        return "tool_node"
    return END


def integrate_tool_outputs(state: FollowUpState) -> dict[str, Any]:
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
        "followup_prompt": _build_prompt(
            state.get("objective", "Prepare a meeting follow-up."),
            context,
            evidence,
        ),
    }


def finalize_followup(state: FollowUpState) -> dict[str, Any]:
    objective = state.get("objective", "Prepare a meeting follow-up.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    prompt = state.get("followup_prompt") or _build_prompt(objective, context, evidence)
    response = llm.invoke([
        SystemMessage(content=FINALIZE_PROMPT),
        HumanMessage(content=prompt),
    ])
    return {"messages": [response]}


builder = StateGraph(FollowUpState)
builder.add_node("ingest_request", ingest_request)
builder.add_node("reasoning_agent", reasoning_agent)
builder.add_node("tool_node", TOOL_NODE)
builder.add_node("integrate_tool_outputs", integrate_tool_outputs)
builder.add_node("finalize_followup", finalize_followup)

builder.add_edge(START, "ingest_request")
builder.add_edge("ingest_request", "reasoning_agent")
builder.add_conditional_edges(
    "reasoning_agent",
    route_after_agent,
    {
        "tool_node": "tool_node",
        "finalize_followup": "finalize_followup",
        END: END,
    },
)
builder.add_edge("tool_node", "integrate_tool_outputs")
builder.add_edge("integrate_tool_outputs", "reasoning_agent")
builder.add_edge("finalize_followup", END)

graph = builder.compile()
