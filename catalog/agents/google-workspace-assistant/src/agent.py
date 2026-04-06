"""LangGraph-based Google Workspace assistant for the RunAgents catalog."""

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


SYSTEM_PROMPT = """You are a Google Workspace assistant operating as a disciplined reasoning workflow.

Help the user work across Gmail, Calendar, Drive, Docs, Sheets, Tasks, and Keep.
Use tools when the current context is incomplete. Avoid redundant tool calls.

Your default behavior is:
- gather only the context needed to answer well
- stay grounded in retrieved evidence
- separate facts from recommendations
- prepare approval-ready actions for writes instead of pretending they already happened

When a write would be required, return a concise approval-ready action with:
- system
- operation
- target
- draft change or payload summary
- why it matters
"""

FINALIZE_PROMPT = """You are finalizing a Google Workspace assistant response after the tool budget was exhausted.

Do not ask for more tools. Produce the best grounded answer possible from the
available context and call out missing information plainly.
"""

MAX_TOOL_ROUNDS = 5


class WorkspaceState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    objective: str
    dossier_prompt: str
    context: dict[str, list[str]]
    evidence: list[str]
    rounds: int


TOOL_SPECS = {
    "gmail": {
        "context_key": "email_context",
        "purpose": "gmail inbox threads, follow-ups, commitments, and draft response context",
        "preferred_fields": ("subject", "title", "summary"),
    },
    "google-calendar": {
        "context_key": "calendar_context",
        "purpose": "google calendar events, attendees, deadlines, and scheduling windows",
        "preferred_fields": ("title", "subject", "name"),
    },
    "google-drive": {
        "context_key": "drive_context",
        "purpose": "google drive files, folders, linked notes, and shared reference material",
        "preferred_fields": ("title", "summary", "name"),
    },
    "google-docs": {
        "context_key": "docs_context",
        "purpose": "google docs content, notes, drafts, agendas, and source documents",
        "preferred_fields": ("title", "summary", "text"),
    },
    "google-sheets": {
        "context_key": "sheets_context",
        "purpose": "google sheets metrics, tables, planning cells, and spreadsheet status context",
        "preferred_fields": ("title", "summary", "sheet", "name"),
    },
    "google-tasks": {
        "context_key": "tasks_context",
        "purpose": "google tasks items, deadlines, ownership, and open action context",
        "preferred_fields": ("title", "task", "summary"),
    },
    "google-keep": {
        "context_key": "keep_context",
        "purpose": "google keep notes, reminders, scratchpad context, and captured ideas",
        "preferred_fields": ("title", "summary", "text"),
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
    for field in ("status", "owner", "due", "decision", "summary", "next_step", "sheet"):
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


def _default_context() -> dict[str, list[str]]:
    return {
        "email_context": [],
        "calendar_context": [],
        "drive_context": [],
        "docs_context": [],
        "sheets_context": [],
        "tasks_context": [],
        "keep_context": [],
    }


def _parse_request(user_prompt: str) -> tuple[str, dict[str, list[str]]]:
    cleaned = _strip_code_fence(user_prompt)
    objective = cleaned or "Help me with my Google Workspace work."
    context = _default_context()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return objective, context

    if not isinstance(payload, dict):
        return objective, context

    objective = str(payload.get("objective") or payload.get("message") or objective).strip() or objective
    context["email_context"] = _coerce_items(
        payload.get("emails") or payload.get("email") or payload.get("email_context"),
        ("subject", "title", "summary"),
    )
    context["calendar_context"] = _coerce_items(
        payload.get("calendar") or payload.get("meetings") or payload.get("calendar_context"),
        ("title", "subject", "name"),
    )
    context["drive_context"] = _coerce_items(
        payload.get("drive") or payload.get("files") or payload.get("drive_context"),
        ("title", "summary", "name"),
    )
    context["docs_context"] = _coerce_items(
        payload.get("docs") or payload.get("documents") or payload.get("docs_context"),
        ("title", "summary", "text"),
    )
    context["sheets_context"] = _coerce_items(
        payload.get("sheets") or payload.get("spreadsheets") or payload.get("sheets_context"),
        ("title", "summary", "sheet", "name"),
    )
    context["tasks_context"] = _coerce_items(
        payload.get("tasks") or payload.get("task_list") or payload.get("tasks_context"),
        ("title", "task", "summary"),
    )
    context["keep_context"] = _coerce_items(
        payload.get("keep") or payload.get("notes") or payload.get("keep_context"),
        ("title", "summary", "text"),
    )
    return objective, context


def _normalize_tool_items(raw: Any, preferred_fields: tuple[str, ...]) -> list[str]:
    if isinstance(raw, dict):
        for key in ("items", "results", "records", "data", "notes", "messages", "documents", "rows", "tasks"):
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
    prompt_lines.extend(_section_lines("Gmail:", context.get("email_context", []), "No Gmail context provided or retrieved."))
    prompt_lines.extend(
        _section_lines("Calendar:", context.get("calendar_context", []), "No Google Calendar context provided or retrieved.")
    )
    prompt_lines.extend(_section_lines("Drive:", context.get("drive_context", []), "No Google Drive context provided or retrieved."))
    prompt_lines.extend(_section_lines("Docs:", context.get("docs_context", []), "No Google Docs context provided or retrieved."))
    prompt_lines.extend(
        _section_lines("Sheets:", context.get("sheets_context", []), "No Google Sheets context provided or retrieved.")
    )
    prompt_lines.extend(_section_lines("Tasks:", context.get("tasks_context", []), "No Google Tasks context provided or retrieved."))
    prompt_lines.extend(_section_lines("Keep:", context.get("keep_context", []), "No Google Keep context provided or retrieved."))
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
                "audience": "google-workspace-assistant",
                "limit": 6,
            },
        )
        items = _normalize_tool_items(response, spec["preferred_fields"])
        if items:
            note = f"Retrieved {len(items)} item(s) from {tool_name}."
        else:
            note = f"{tool_name} responded but returned no reusable Google Workspace context."
    except Exception as exc:
        items = []
        note = f"{tool_name} retrieval unavailable: {exc}"

    return json.dumps({
        "tool": tool_name,
        "context_key": spec["context_key"],
        "items": items,
        "note": note,
    })


@tool("gmail", description="Retrieve Gmail inbox threads, follow-ups, and message context.")
def email_tool(objective: str) -> str:
    return _call_managed_tool("gmail", objective)


@tool("google-calendar", description="Retrieve Google Calendar events, attendees, and schedule context.")
def calendar_tool(objective: str) -> str:
    return _call_managed_tool("google-calendar", objective)


@tool("google-drive", description="Retrieve Google Drive files, folders, and shared reference material.")
def drive_tool(objective: str) -> str:
    return _call_managed_tool("google-drive", objective)


@tool("google-docs", description="Retrieve Google Docs notes, drafts, agendas, and source content.")
def docs_tool(objective: str) -> str:
    return _call_managed_tool("google-docs", objective)


@tool("google-sheets", description="Retrieve Google Sheets metrics, tables, and spreadsheet planning context.")
def sheets_tool(objective: str) -> str:
    return _call_managed_tool("google-sheets", objective)


@tool("google-tasks", description="Retrieve Google Tasks items, due dates, and action context.")
def tasks_tool(objective: str) -> str:
    return _call_managed_tool("google-tasks", objective)


@tool("google-keep", description="Retrieve Google Keep notes, reminders, and captured ideas.")
def keep_tool(objective: str) -> str:
    return _call_managed_tool("google-keep", objective)


WORKSPACE_TOOLS = [
    email_tool,
    calendar_tool,
    drive_tool,
    docs_tool,
    sheets_tool,
    tasks_tool,
    keep_tool,
]
TOOL_NODE = ToolNode(WORKSPACE_TOOLS)
AGENT_LLM = llm.bind_tools(WORKSPACE_TOOLS)


def ingest_request(state: WorkspaceState) -> dict[str, Any]:
    message = ""
    if state.get("messages"):
        message = _message_text(state["messages"][-1])
    objective, context = _parse_request(message)

    evidence = [f"Workspace objective: {objective}"]
    for tool_name, spec in TOOL_SPECS.items():
        items = context.get(spec["context_key"], [])
        if items:
            evidence.append(f"Used {len(items)} {tool_name} item(s) provided in the request.")

    return {
        "objective": objective,
        "dossier_prompt": _build_prompt(objective, context, evidence),
        "context": context,
        "evidence": evidence,
        "rounds": 0,
    }


def reasoning_agent(state: WorkspaceState) -> dict[str, Any]:
    objective = state.get("objective", "Help me with my Google Workspace work.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    dossier_prompt = state.get("dossier_prompt") or _build_prompt(objective, context, evidence)

    history = [
        message
        for message in state.get("messages", [])
        if isinstance(message, (AIMessage, ToolMessage))
    ]

    response = AGENT_LLM.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=dossier_prompt),
            *history,
        ]
    )
    return {
        "messages": [response],
        "rounds": state.get("rounds", 0) + 1,
    }


def route_after_agent(state: WorkspaceState) -> str:
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        if state.get("rounds", 0) >= MAX_TOOL_ROUNDS:
            return "finalize_response"
        return "tool_node"
    return END


def integrate_tool_outputs(state: WorkspaceState) -> dict[str, Any]:
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
        "dossier_prompt": _build_prompt(
            state.get("objective", "Help me with my Google Workspace work."),
            context,
            evidence,
        ),
    }


def finalize_response(state: WorkspaceState) -> dict[str, Any]:
    objective = state.get("objective", "Help me with my Google Workspace work.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    dossier_prompt = state.get("dossier_prompt") or _build_prompt(objective, context, evidence)

    response = llm.invoke(
        [
            SystemMessage(content=FINALIZE_PROMPT),
            HumanMessage(content=dossier_prompt),
        ]
    )
    return {"messages": [response]}


builder = StateGraph(WorkspaceState)
builder.add_node("ingest_request", ingest_request)
builder.add_node("reasoning_agent", reasoning_agent)
builder.add_node("tool_node", TOOL_NODE)
builder.add_node("integrate_tool_outputs", integrate_tool_outputs)
builder.add_node("finalize_response", finalize_response)

builder.add_edge(START, "ingest_request")
builder.add_edge("ingest_request", "reasoning_agent")
builder.add_conditional_edges(
    "reasoning_agent",
    route_after_agent,
    {
        "tool_node": "tool_node",
        "finalize_response": "finalize_response",
        END: END,
    },
)
builder.add_edge("tool_node", "integrate_tool_outputs")
builder.add_edge("integrate_tool_outputs", "reasoning_agent")
builder.add_edge("finalize_response", END)

graph = builder.compile()
