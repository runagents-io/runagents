"""LangGraph-based chief of staff workflow for the RunAgents catalog.

This example focuses on the strongest enterprise pattern available in the
current RunAgents runtime:
- gather context from multiple external tools
- reason across executive priorities, meetings, customer signals, and follow-ups
- produce clear drafts and approval-ready actions
- keep all tool access inside RunAgents-managed routing

The graph is intentionally conservative about writes. It prepares exact,
approval-ready actions for email, chat, tasks, CRM, calendar, and WhatsApp,
while leaving final execution to RunAgents approval flows.
"""

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


SYSTEM_PROMPT = """You are a chief of staff assistant operating as a disciplined LangGraph reasoning workflow.

Your job is to help a leader or operator stay ahead of their day. You can:
- prepare a morning priorities brief
- prepare meeting prep material
- synthesize meeting follow-up and action items
- summarize customer interactions and account risk
- prepare end-of-day or weekly digests
- draft approval-ready actions across email, team chat, calendar, task systems, CRM, and WhatsApp

Use the available tools when important context is missing. Avoid redundant tool calls.
Stay grounded in retrieved evidence and distinguish facts from recommendations.

When the user asks for a write action, do not pretend it has already happened.
Instead, prepare an approval-ready action with:
- system
- operation
- target
- concise draft or payload summary
- why it matters
- suggested approval lane (UI, Slack, WhatsApp, or iMessage)
- delegated identity expectation when relevant

Default to the lightest set of tool calls needed to produce a credible result.
"""

FINALIZE_PROMPT = """You are finalizing a chief of staff response after the tool budget was exhausted.

Do not ask for more tools. Produce the best possible grounded result using the
current context. If the user asked for a write, return an approval-ready action
instead of claiming execution.
"""

MAX_TOOL_ROUNDS = 5

MODE_GUIDANCE = {
    "morning-priorities": "Focus on today's top priorities, critical meetings, urgent follow-ups, and near-term risks.",
    "meeting-prep": "Focus on meeting objective, participants, prior context, risks, and a sharp prep brief.",
    "meeting-follow-up": "Focus on decisions, action items, owners, deadlines, and the draft follow-up.",
    "customer-summary": "Focus on customer sentiment, commitments, blockers, open risks, and the recommended next move.",
    "end-of-day": "Focus on what moved today, what slipped, unresolved threads, and tomorrow's first moves.",
    "weekly-digest": "Focus on strategic progress, unresolved decisions, key stakeholder dynamics, and next week's priorities.",
    "general-chief-of-staff": "Focus on the user's stated need, cross-functional context, priorities, and approval-ready next actions.",
}


class ChiefOfStaffState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    mode: str
    objective: str
    delivery_lanes: list[str]
    dossier_prompt: str
    context: dict[str, list[str]]
    evidence: list[str]
    rounds: int


TOOL_SPECS = {
    "calendar": {
        "context_key": "schedule_context",
        "purpose": "calendar events, leadership cadence, scheduling windows, and meeting timing",
        "preferred_fields": ("title", "subject", "name"),
    },
    "email": {
        "context_key": "inbox_context",
        "purpose": "priority email threads, follow-ups, and external communications context",
        "preferred_fields": ("subject", "title", "summary"),
    },
    "drive": {
        "context_key": "document_context",
        "purpose": "working docs, decks, notes, and reference material from drive systems",
        "preferred_fields": ("title", "summary", "text"),
    },
    "team-chat": {
        "context_key": "collaboration_context",
        "purpose": "Slack or Teams signals, mentions, executive chatter, and internal follow-up context",
        "preferred_fields": ("signal", "summary", "text", "channel"),
    },
    "project-tracker": {
        "context_key": "execution_context",
        "purpose": "tasks, blockers, owners, deadlines, and delivery progress",
        "preferred_fields": ("title", "task", "summary"),
    },
    "meeting-notes": {
        "context_key": "meeting_context",
        "purpose": "meeting notes, transcripts, decision logs, and captured action items",
        "preferred_fields": ("title", "summary", "decision", "text"),
    },
    "crm": {
        "context_key": "customer_context",
        "purpose": "account state, customer risk, opportunities, contact context, and relationship history",
        "preferred_fields": ("account", "title", "summary", "name"),
    },
    "knowledge-base": {
        "context_key": "reference_context",
        "purpose": "internal policies, playbooks, and organizational reference context",
        "preferred_fields": ("title", "summary", "text"),
    },
    "whatsapp": {
        "context_key": "mobile_context",
        "purpose": "mobile command thread context, brief delivery preferences, and executive lane follow-up state",
        "preferred_fields": ("summary", "text", "message", "signal"),
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
    for field in (
        "status",
        "decision",
        "owner",
        "due",
        "next_step",
        "signal",
        "urgency",
        "channel",
    ):
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


def _infer_mode(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("morning", "today", "top priorities", "top things")):
        return "morning-priorities"
    if any(token in lowered for token in ("prep", "prepare me for", "before my meeting", "brief me for")):
        return "meeting-prep"
    if any(token in lowered for token in ("follow-up", "follow up", "recap", "meeting notes", "action items")):
        return "meeting-follow-up"
    if any(token in lowered for token in ("customer", "account", "renewal", "escalation", "deal", "prospect")):
        return "customer-summary"
    if any(token in lowered for token in ("end of day", "eod", "summary of the day", "today summary")):
        return "end-of-day"
    if any(token in lowered for token in ("weekly", "week ahead", "weekly digest")):
        return "weekly-digest"
    return "general-chief-of-staff"


def _normalize_delivery_lanes(raw: Any) -> list[str]:
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, list):
        items = raw
    else:
        items = []
    normalized: list[str] = []
    for item in items:
        text = str(item).strip().lower()
        if not text:
            continue
        if text not in normalized:
            normalized.append(text)
    return normalized


def _default_context() -> dict[str, list[str]]:
    return {
        "schedule_context": [],
        "inbox_context": [],
        "document_context": [],
        "collaboration_context": [],
        "execution_context": [],
        "meeting_context": [],
        "customer_context": [],
        "reference_context": [],
        "mobile_context": [],
    }


def _parse_request(user_prompt: str) -> tuple[str, str, dict[str, list[str]], list[str]]:
    cleaned = _strip_code_fence(user_prompt)
    objective = cleaned or "Act as my chief of staff for today."
    mode = _infer_mode(objective)
    delivery_lanes: list[str] = []
    context = _default_context()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return mode, objective, context, delivery_lanes

    if not isinstance(payload, dict):
        return mode, objective, context, delivery_lanes

    objective = str(payload.get("objective") or payload.get("message") or objective).strip() or objective
    mode = str(payload.get("mode") or mode).strip() or mode
    delivery_lanes = _normalize_delivery_lanes(
        payload.get("delivery_lanes") or payload.get("delivery_preferences") or payload.get("channels")
    )

    context["schedule_context"] = _coerce_items(
        payload.get("schedule") or payload.get("calendar") or payload.get("schedule_context"),
        ("title", "subject", "name"),
    )
    context["inbox_context"] = _coerce_items(
        payload.get("emails") or payload.get("inbox") or payload.get("inbox_context"),
        ("subject", "title", "summary"),
    )
    context["document_context"] = _coerce_items(
        payload.get("docs") or payload.get("documents") or payload.get("document_context"),
        ("title", "summary", "text"),
    )
    context["collaboration_context"] = _coerce_items(
        payload.get("chat") or payload.get("messages") or payload.get("collaboration_context"),
        ("signal", "summary", "text", "channel"),
    )
    context["execution_context"] = _coerce_items(
        payload.get("tasks") or payload.get("projects") or payload.get("execution_context"),
        ("title", "task", "summary"),
    )
    context["meeting_context"] = _coerce_items(
        payload.get("meeting_notes") or payload.get("meetings") or payload.get("meeting_context"),
        ("title", "summary", "decision", "text"),
    )
    context["customer_context"] = _coerce_items(
        payload.get("customer") or payload.get("crm") or payload.get("customer_context"),
        ("account", "title", "summary", "name"),
    )
    context["reference_context"] = _coerce_items(
        payload.get("reference") or payload.get("knowledge") or payload.get("reference_context"),
        ("title", "summary", "text"),
    )
    context["mobile_context"] = _coerce_items(
        payload.get("whatsapp") or payload.get("mobile") or payload.get("mobile_context"),
        ("summary", "text", "message", "signal"),
    )
    return mode, objective, context, delivery_lanes


def _normalize_tool_items(raw: Any, preferred_fields: tuple[str, ...]) -> list[str]:
    if isinstance(raw, dict):
        for key in (
            "items",
            "results",
            "records",
            "data",
            "messages",
            "threads",
            "notes",
            "tasks",
            "events",
            "documents",
            "accounts",
        ):
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


def _build_dossier_prompt(mode: str, objective: str, context: dict[str, list[str]], evidence: list[str], delivery_lanes: list[str]) -> str:
    prompt_lines = [
        f"Mode: {mode}",
        f"Objective: {objective}",
        f"Mode guidance: {MODE_GUIDANCE.get(mode, MODE_GUIDANCE['general-chief-of-staff'])}",
        f"Preferred delivery lanes: {', '.join(delivery_lanes) if delivery_lanes else 'ui, slack, or whatsapp as appropriate'}",
        "",
    ]
    prompt_lines.extend(_section_lines("Schedule context:", context.get("schedule_context", []), "No schedule context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Inbox context:", context.get("inbox_context", []), "No inbox context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Document context:", context.get("document_context", []), "No document context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Collaboration context:", context.get("collaboration_context", []), "No Slack or Teams context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Execution context:", context.get("execution_context", []), "No task or delivery context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Meeting context:", context.get("meeting_context", []), "No meeting notes context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Customer context:", context.get("customer_context", []), "No customer or CRM context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Reference context:", context.get("reference_context", []), "No policy or playbook context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Mobile lane context:", context.get("mobile_context", []), "No WhatsApp or mobile lane context was provided or retrieved."))
    prompt_lines.extend(_section_lines("Evidence trail:", evidence, "No evidence trail captured."))
    return "\n".join(prompt_lines)


def _call_managed_tool(tool_name: str, objective: str, mode: str, delivery_lanes: list[str]) -> str:
    spec = TOOL_SPECS[tool_name]
    try:
        response = tool_client.call_tool(
            tool_name,
            payload={
                "objective": objective,
                "mode": mode,
                "purpose": spec["purpose"],
                "audience": "chief-of-staff",
                "delivery_lanes": delivery_lanes,
                "limit": 6,
            },
        )
        items = _normalize_tool_items(response, spec["preferred_fields"])
        if items:
            note = f"Retrieved {len(items)} item(s) from {tool_name}."
        else:
            note = f"{tool_name} responded but returned no reusable chief-of-staff context."
    except Exception as exc:
        items = []
        note = f"{tool_name} retrieval unavailable: {exc}"

    return json.dumps({
        "tool": tool_name,
        "context_key": spec["context_key"],
        "items": items,
        "note": note,
    })


@tool("calendar", description="Retrieve calendar context, meeting timing, and executive schedule signals.")
def calendar_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("calendar", objective, mode, [])


@tool("email", description="Retrieve email threads, inbox priorities, and follow-up context.")
def email_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("email", objective, mode, [])


@tool("drive", description="Retrieve working docs, notes, decks, and drive-based reference material.")
def drive_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("drive", objective, mode, [])


@tool("team-chat", description="Retrieve Slack or Teams mentions, threads, and collaboration signals.")
def team_chat_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("team-chat", objective, mode, [])


@tool("project-tracker", description="Retrieve project tasks, blockers, owners, and due dates.")
def project_tracker_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("project-tracker", objective, mode, [])


@tool("meeting-notes", description="Retrieve meeting notes, transcripts, decisions, and action-item context.")
def meeting_notes_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("meeting-notes", objective, mode, [])


@tool("crm", description="Retrieve customer, account, and relationship context from CRM systems.")
def crm_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("crm", objective, mode, [])


@tool("knowledge-base", description="Retrieve internal policies, playbooks, and supporting reference material.")
def knowledge_base_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("knowledge-base", objective, mode, [])


@tool("whatsapp", description="Retrieve mobile lane command context and WhatsApp-based briefing state.")
def whatsapp_tool(objective: str, mode: str = "general-chief-of-staff") -> str:
    return _call_managed_tool("whatsapp", objective, mode, ["whatsapp"])


CHIEF_OF_STAFF_TOOLS = [
    calendar_tool,
    email_tool,
    drive_tool,
    team_chat_tool,
    project_tracker_tool,
    meeting_notes_tool,
    crm_tool,
    knowledge_base_tool,
    whatsapp_tool,
]
TOOL_NODE = ToolNode(CHIEF_OF_STAFF_TOOLS)
AGENT_LLM = llm.bind_tools(CHIEF_OF_STAFF_TOOLS)


def ingest_request(state: ChiefOfStaffState) -> dict[str, Any]:
    message = _message_text(state.get("messages", [])[-1]) if state.get("messages") else ""
    mode, objective, context, delivery_lanes = _parse_request(message)

    evidence = [
        f"Chief of staff objective: {objective}",
        f"Operating mode: {mode}",
    ]
    if delivery_lanes:
        evidence.append(f"Requested delivery lanes: {', '.join(delivery_lanes)}")

    for tool_name, spec in TOOL_SPECS.items():
        items = context.get(spec["context_key"], [])
        if items:
            evidence.append(f"Used {len(items)} {tool_name} signal(s) supplied in the request payload.")

    return {
        "mode": mode,
        "objective": objective,
        "delivery_lanes": delivery_lanes,
        "context": context,
        "evidence": evidence,
        "dossier_prompt": _build_dossier_prompt(mode, objective, context, evidence, delivery_lanes),
        "rounds": 0,
    }


def reasoning_agent(state: ChiefOfStaffState) -> dict[str, Any]:
    mode = state.get("mode", "general-chief-of-staff")
    objective = state.get("objective", "Act as my chief of staff for today.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    delivery_lanes = state.get("delivery_lanes", [])
    prompt = state.get("dossier_prompt") or _build_dossier_prompt(mode, objective, context, evidence, delivery_lanes)
    history = [message for message in state.get("messages", []) if isinstance(message, (AIMessage, ToolMessage))]

    response = AGENT_LLM.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
        *history,
    ])
    return {"messages": [response], "rounds": state.get("rounds", 0) + 1}


def route_after_agent(state: ChiefOfStaffState) -> str:
    messages = state.get("messages", [])
    if messages and getattr(messages[-1], "tool_calls", None):
        if state.get("rounds", 0) >= MAX_TOOL_ROUNDS:
            return "finalize_response"
        return "tool_node"
    return END


def integrate_tool_outputs(state: ChiefOfStaffState) -> dict[str, Any]:
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

    mode = state.get("mode", "general-chief-of-staff")
    objective = state.get("objective", "Act as my chief of staff for today.")
    delivery_lanes = state.get("delivery_lanes", [])
    return {
        "context": context,
        "evidence": evidence,
        "dossier_prompt": _build_dossier_prompt(mode, objective, context, evidence, delivery_lanes),
    }


def finalize_response(state: ChiefOfStaffState) -> dict[str, Any]:
    mode = state.get("mode", "general-chief-of-staff")
    objective = state.get("objective", "Act as my chief of staff for today.")
    context = state.get("context", {})
    evidence = state.get("evidence", [])
    delivery_lanes = state.get("delivery_lanes", [])
    prompt = state.get("dossier_prompt") or _build_dossier_prompt(mode, objective, context, evidence, delivery_lanes)

    response = llm.invoke([
        SystemMessage(content=FINALIZE_PROMPT),
        HumanMessage(
            content=(
                f"{prompt}\n\n"
                "Produce a high-utility chief of staff response with these sections:\n"
                "1. Executive Summary\n"
                "2. What Matters Most Right Now\n"
                "3. Meetings, Stakeholders, And Customer Signals\n"
                "4. Drafted Actions\n"
                "5. Approval Queue\n"
                "6. Suggested Delivery Lane\n\n"
                "Rules:\n"
                "- Never claim a write already happened.\n"
                "- In 'Approval Queue', include exact approval-ready actions when the user asked to send, post, schedule, update, or create.\n"
                "- For each proposed action include: system, operation, target, concise draft/payload, why it matters, and the best approval lane.\n"
                "- Prefer WhatsApp when the request mentions mobile, urgency, end-of-day summaries, or executive convenience.\n"
                "- If there is not enough evidence for a write, say what is missing.\n"
            )
        ),
    ])
    return {"messages": [response]}


builder = StateGraph(ChiefOfStaffState)
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
