"""LangGraph-based Google Workspace assistant for the RunAgents catalog."""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, TypedDict
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from runagents import Agent, ToolNotConfigured
from runagents.runtime import ConsentRequired


SYSTEM_PROMPT = """You are a Google Workspace assistant operating as a disciplined reasoning workflow.

Help the user work across Gmail, Calendar, Drive, Docs, Sheets, Tasks, and Keep.
Use tools when the current context is incomplete. Avoid redundant tool calls.

Prefer explicit tool choices over vague retrieval:
- for email questions, first use gmail_list_messages to find candidates, then gmail_get_message for the specific email you need
- for meeting questions, use calendar_list_events
- for explicit scheduling requests with clear details, use calendar_create_event
- for file and document questions, use drive_list_files to find IDs before calling docs_get_document or sheets_* tools
- for spreadsheet questions, use sheets_get_spreadsheet for structure and sheets_read_range for cell values
- for task questions, use tasks_list_tasklists and tasks_list_tasks
- for note questions, use keep_list_notes

Your default behavior is:
- gather only the context needed to answer well
- stay grounded in retrieved evidence
- separate facts from recommendations
- use explicit write tools only when the user has given enough detail and the action is appropriate
- otherwise prepare approval-ready actions instead of pretending writes already happened

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

MAX_TOOL_ROUNDS = 6
MAX_LIST_ITEMS = 8
MAX_TEXT_CHARS = 1800


class WorkspaceState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    objective: str
    dossier_prompt: str
    context: dict[str, list[str]]
    evidence: list[str]
    rounds: int


TOOL_SPECS = {
    "email_context": {
        "title": "Gmail:",
        "empty": "No Gmail context provided or retrieved.",
    },
    "calendar_context": {
        "title": "Calendar:",
        "empty": "No Google Calendar context provided or retrieved.",
    },
    "drive_context": {
        "title": "Drive:",
        "empty": "No Google Drive context provided or retrieved.",
    },
    "docs_context": {
        "title": "Docs:",
        "empty": "No Google Docs context provided or retrieved.",
    },
    "sheets_context": {
        "title": "Sheets:",
        "empty": "No Google Sheets context provided or retrieved.",
    },
    "tasks_context": {
        "title": "Tasks:",
        "empty": "No Google Tasks context provided or retrieved.",
    },
    "keep_context": {
        "title": "Keep:",
        "empty": "No Google Keep context provided or retrieved.",
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
        items = [_stringify_item(item, preferred_fields) for item in value[:MAX_LIST_ITEMS]]
        return [item for item in items if item]
    text = _stringify_item(value, preferred_fields)
    return [text] if text else []


def _default_context() -> dict[str, list[str]]:
    return {key: [] for key in TOOL_SPECS}


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


def _section_lines(title: str, items: list[str], empty_message: str) -> list[str]:
    lines = [title]
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append(f"- {empty_message}")
    lines.append("")
    return lines


def _build_prompt(objective: str, context: dict[str, list[str]], evidence: list[str]) -> str:
    now_utc = _utc_now()
    now_local = now_utc.astimezone()
    local_tz = now_local.tzname() or "local"
    prompt_lines = [
        f"Objective: {objective}",
        f"Current UTC time: {now_utc.isoformat().replace('+00:00', 'Z')}",
        f"Current local time: {now_local.isoformat()} ({local_tz})",
        "",
    ]
    for context_key, spec in TOOL_SPECS.items():
        prompt_lines.extend(_section_lines(spec["title"], context.get(context_key, []), spec["empty"]))
    prompt_lines.extend(_section_lines("Evidence trail:", evidence, "No evidence trail captured."))
    return "\n".join(prompt_lines)


def _truncate_text(text: str, limit: int = MAX_TEXT_CHARS) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _encode_query(params: dict[str, Any]) -> str:
    filtered: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, str):
            if not value.strip():
                continue
            filtered[key] = value.strip()
            continue
        filtered[key] = value
    if not filtered:
        return ""
    return "?" + urlencode(filtered, doseq=True)


def _build_path(path: str, **params: Any) -> str:
    return path + _encode_query(params)


def _note(tool_name: str, action: str, count: int) -> str:
    return f"{tool_name}: {action} ({count} item(s))."


def _tool_payload(tool_name: str, context_key: str, items: list[str], note: str) -> str:
    return json.dumps(
        {
            "tool": tool_name,
            "context_key": context_key,
            "items": items[:MAX_LIST_ITEMS],
            "note": note,
        }
    )


def _tool_payload_with_error(
    tool_name: str,
    context_key: str,
    items: list[str],
    note: str,
    *,
    error_code: str = "",
    authorization_url: str = "",
    detail: str = "",
    message: str = "",
) -> str:
    payload = {
        "tool": tool_name,
        "context_key": context_key,
        "items": items[:MAX_LIST_ITEMS],
        "note": note,
    }
    if error_code:
        payload["error_code"] = error_code
    if authorization_url:
        payload["authorization_url"] = authorization_url
    if detail:
        payload["detail"] = detail
    if message:
        payload["message"] = message
    return json.dumps(payload)


def _parse_error_info(result: Any) -> dict[str, str]:
    if not isinstance(result, dict) or not result.get("error"):
        return {}

    error = str(result.get("error") or "").strip()
    detail = str(result.get("detail") or error or "tool call failed").strip()
    authorization_url = str(result.get("authorization_url") or "").strip()

    if error == "CONSENT_REQUIRED":
        message = "You need to connect Google access before I can continue."
        if authorization_url:
            message += f" {authorization_url}"
        return {
            "code": "CONSENT_REQUIRED",
            "detail": detail or "User must grant OAuth consent for this tool",
            "authorization_url": authorization_url,
            "message": message,
        }

    if error.startswith("HTTP 429"):
        return {
            "code": "HTTP_429",
            "detail": detail or "Google temporarily rate limited this request",
            "message": "Google temporarily rate limited that request. Please wait a minute and try again.",
        }

    if error.startswith("HTTP "):
        return {
            "code": error.replace(" ", "_"),
            "detail": detail,
            "message": detail,
        }

    return {
        "code": "TOOL_ERROR",
        "detail": detail,
        "authorization_url": authorization_url,
        "message": detail,
    }


def _call_workspace_api(
    managed_tool_name: str,
    *,
    path: str = "/",
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, str]]:
    try:
        result = tool_client.call_tool(managed_tool_name, path=path, payload=payload, method=method)
    except ConsentRequired:
        raise
    except ToolNotConfigured as exc:
        return {}, {
            "code": "TOOL_NOT_CONFIGURED",
            "detail": f"{managed_tool_name} is not configured for this agent: {exc}",
            "message": f"{managed_tool_name} is not configured for this agent.",
        }
    except Exception as exc:
        return {}, {
            "code": "TOOL_CALL_FAILED",
            "detail": f"{managed_tool_name} call failed: {exc}",
            "message": f"{managed_tool_name} call failed.",
        }

    error_info = _parse_error_info(result)
    if error_info:
        return result, error_info
    return result, {}


def _decode_base64url(data: str) -> str:
    if not data:
        return ""
    padded = data + "=" * ((4 - len(data) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return decoded.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_gmail_body(payload: dict[str, Any]) -> str:
    body = payload.get("body") or {}
    data = body.get("data")
    if isinstance(data, str) and data:
        return _decode_base64url(data)
    for part in payload.get("parts") or []:
        mime_type = str(part.get("mimeType") or "")
        if mime_type.startswith("text/plain"):
            nested = _extract_gmail_body(part)
            if nested:
                return nested
    return ""


def _gmail_headers(message_payload: dict[str, Any]) -> dict[str, str]:
    headers = {}
    for header in message_payload.get("headers") or []:
        name = str(header.get("name") or "").lower()
        value = str(header.get("value") or "").strip()
        if name and value:
            headers[name] = value
    return headers


def _format_gmail_message_list(response: Any) -> list[str]:
    messages = []
    if isinstance(response, dict):
        messages = response.get("messages") or []
    items: list[str] = []
    for msg in messages[:MAX_LIST_ITEMS]:
        msg_id = str(msg.get("id") or "").strip()
        thread_id = str(msg.get("threadId") or "").strip()
        if not msg_id:
            continue
        suffix = f" (thread {thread_id})" if thread_id else ""
        items.append(f"message_id={msg_id}{suffix}")
    return items


def _format_gmail_message(response: Any) -> list[str]:
    if not isinstance(response, dict):
        return []
    payload = response.get("payload") or {}
    headers = _gmail_headers(payload)
    snippet = _truncate_text(str(response.get("snippet") or ""), 280)
    body_text = _truncate_text(_extract_gmail_body(payload), 700)
    parts = [
        f"subject: {headers.get('subject', '(no subject)')}",
        f"from: {headers.get('from', 'unknown')}",
        f"date: {headers.get('date', 'unknown')}",
    ]
    if snippet:
        parts.append(f"snippet: {snippet}")
    if body_text:
        parts.append(f"body: {body_text}")
    return [" | ".join(parts)]


def _format_calendar_events(response: Any) -> list[str]:
    events = response.get("items") if isinstance(response, dict) else []
    items: list[str] = []
    for event in (events or [])[:MAX_LIST_ITEMS]:
        start = (event.get("start") or {}).get("dateTime") or (event.get("start") or {}).get("date") or "unscheduled"
        end = (event.get("end") or {}).get("dateTime") or (event.get("end") or {}).get("date") or ""
        title = str(event.get("summary") or "Untitled event")
        attendees = []
        for attendee in (event.get("attendees") or [])[:3]:
            email = str(attendee.get("email") or "").strip()
            if email:
                attendees.append(email)
        suffix = f" | attendees: {', '.join(attendees)}" if attendees else ""
        if end:
            items.append(f"{title} | {start} -> {end}{suffix}")
        else:
            items.append(f"{title} | {start}{suffix}")
    return items


def _format_calendar_write_result(response: Any) -> list[str]:
    if not isinstance(response, dict):
        return []
    start = (response.get("start") or {}).get("dateTime") or (response.get("start") or {}).get("date") or "unscheduled"
    end = (response.get("end") or {}).get("dateTime") or (response.get("end") or {}).get("date") or ""
    title = str(response.get("summary") or "Untitled event")
    event_id = str(response.get("id") or "").strip()
    status = str(response.get("status") or "").strip()
    html_link = str(response.get("htmlLink") or "").strip()
    parts = [title]
    if event_id:
        parts.append(f"id: {event_id}")
    if end:
        parts.append(f"time: {start} -> {end}")
    else:
        parts.append(f"time: {start}")
    if status:
        parts.append(f"status: {status}")
    if html_link:
        parts.append(f"link: {html_link}")
    return [" | ".join(parts)]


def _format_drive_files(response: Any) -> list[str]:
    files = response.get("files") if isinstance(response, dict) else []
    items: list[str] = []
    for file in (files or [])[:MAX_LIST_ITEMS]:
        file_id = str(file.get("id") or "").strip()
        name = str(file.get("name") or "Unnamed file")
        mime_type = str(file.get("mimeType") or "unknown")
        modified = str(file.get("modifiedTime") or "")
        suffix = f" | modified: {modified}" if modified else ""
        items.append(f"{name} | id: {file_id} | type: {mime_type}{suffix}")
    return items


def _extract_doc_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    body = response.get("body") or {}
    for element in body.get("content") or []:
        paragraph = element.get("paragraph") or {}
        for part in paragraph.get("elements") or []:
            text_run = part.get("textRun") or {}
            content = str(text_run.get("content") or "")
            if content:
                chunks.append(content)
    return _truncate_text("".join(chunks), 1000)


def _format_document(response: Any) -> list[str]:
    if not isinstance(response, dict):
        return []
    title = str(response.get("title") or "Untitled document")
    doc_id = str(response.get("documentId") or "")
    text = _extract_doc_text(response)
    summary = f"{title} | id: {doc_id}"
    if text:
        summary += f" | excerpt: {text}"
    return [summary]


def _format_spreadsheet(response: Any) -> list[str]:
    if not isinstance(response, dict):
        return []
    props = response.get("properties") or {}
    title = str(props.get("title") or "Untitled spreadsheet")
    spreadsheet_id = str(response.get("spreadsheetId") or "")
    sheet_names = []
    for sheet in (response.get("sheets") or [])[:10]:
        sheet_props = sheet.get("properties") or {}
        name = str(sheet_props.get("title") or "").strip()
        if name:
            sheet_names.append(name)
    suffix = f" | sheets: {', '.join(sheet_names)}" if sheet_names else ""
    return [f"{title} | id: {spreadsheet_id}{suffix}"]


def _format_sheet_values(response: Any) -> list[str]:
    if not isinstance(response, dict):
        return []
    range_name = str(response.get("range") or "")
    values = response.get("values") or []
    rows: list[str] = []
    for row in values[:10]:
        if isinstance(row, list):
            rows.append(" | ".join(str(cell) for cell in row))
    if not rows:
        rows.append("No values returned.")
    return [f"range: {range_name}"] + rows


def _format_tasklists(response: Any) -> list[str]:
    lists = response.get("items") if isinstance(response, dict) else []
    items: list[str] = []
    for tasklist in (lists or [])[:MAX_LIST_ITEMS]:
        tasklist_id = str(tasklist.get("id") or "").strip()
        title = str(tasklist.get("title") or "Untitled task list")
        updated = str(tasklist.get("updated") or "")
        suffix = f" | updated: {updated}" if updated else ""
        items.append(f"{title} | id: {tasklist_id}{suffix}")
    return items


def _format_tasks(response: Any) -> list[str]:
    tasks = response.get("items") if isinstance(response, dict) else []
    items: list[str] = []
    for task in (tasks or [])[:MAX_LIST_ITEMS]:
        title = str(task.get("title") or "Untitled task")
        task_id = str(task.get("id") or "").strip()
        status = str(task.get("status") or "unknown")
        due = str(task.get("due") or "")
        notes = _truncate_text(str(task.get("notes") or ""), 240)
        parts = [f"{title}", f"id: {task_id}", f"status: {status}"]
        if due:
            parts.append(f"due: {due}")
        if notes:
            parts.append(f"notes: {notes}")
        items.append(" | ".join(parts))
    return items


def _format_keep_notes(response: Any) -> list[str]:
    notes = response.get("notes") if isinstance(response, dict) else []
    items: list[str] = []
    for note in (notes or [])[:MAX_LIST_ITEMS]:
        title = str(note.get("title") or "Untitled note")
        note_name = str(note.get("name") or "").strip()
        body = note.get("body") or {}
        text = _truncate_text(((body.get("text") or {}).get("content") or ""), 260)
        parts = [f"{title}", f"name: {note_name}"]
        if text:
            parts.append(f"text: {text}")
        items.append(" | ".join(parts))
    return items


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_event_datetime(value: str, time_zone: str = "") -> datetime:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("start and end times must be ISO 8601 values")
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is not None:
        return parsed
    tz_name = time_zone.strip()
    if tz_name:
        try:
            return parsed.replace(tzinfo=ZoneInfo(tz_name))
        except Exception as exc:
            raise ValueError(f"unknown time zone: {tz_name}") from exc
    return parsed.replace(tzinfo=timezone.utc)


def _calendar_event_time_payload(moment: datetime, time_zone: str = "") -> dict[str, str]:
    payload = {"dateTime": moment.isoformat().replace("+00:00", "Z")}
    tz_name = time_zone.strip()
    if tz_name:
        payload["timeZone"] = tz_name
    return payload


@tool("gmail_list_messages", description="Search Gmail for relevant messages. Use this first when you need candidate email IDs before reading a specific email.")
def gmail_list_messages(query: str = "", max_results: int = 5) -> str:
    response, error_info = _call_workspace_api(
        "email",
        method="GET",
        path=_build_path("/gmail/v1/users/me/messages", maxResults=max(1, min(max_results, 10)), q=query),
    )
    items = _format_gmail_message_list(response)
    note = error_info.get("detail") or _note("gmail_list_messages", "searched Gmail", len(items))
    return _tool_payload_with_error(
        "gmail_list_messages",
        "email_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("gmail_get_message", description="Read a specific Gmail message by message ID after identifying the right candidate email.")
def gmail_get_message(message_id: str) -> str:
    response, error_info = _call_workspace_api(
        "email",
        method="GET",
        path=_build_path(f"/gmail/v1/users/me/messages/{quote(message_id.strip(), safe='')}", format="full"),
    )
    items = _format_gmail_message(response)
    note = error_info.get("detail") or _note("gmail_get_message", "read Gmail message", len(items))
    return _tool_payload_with_error(
        "gmail_get_message",
        "email_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("calendar_list_events", description="List Google Calendar events in a time window. Use for schedule, meeting, and deadline questions.")
def calendar_list_events(query: str = "", start_iso: str = "", end_iso: str = "", max_results: int = 8) -> str:
    now = _utc_now()
    time_min = start_iso.strip() or now.isoformat().replace("+00:00", "Z")
    time_max = end_iso.strip() or (now + timedelta(days=7)).isoformat().replace("+00:00", "Z")
    response, error_info = _call_workspace_api(
        "calendar",
        method="GET",
        path=_build_path(
            "/calendar/v3/calendars/primary/events",
            singleEvents="true",
            orderBy="startTime",
            maxResults=max(1, min(max_results, 10)),
            q=query,
            timeMin=time_min,
            timeMax=time_max,
        ),
    )
    items = _format_calendar_events(response)
    note = error_info.get("detail") or _note("calendar_list_events", "listed calendar events", len(items))
    return _tool_payload_with_error(
        "calendar_list_events",
        "calendar_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("calendar_create_event", description="Create a Google Calendar event when the user explicitly wants to schedule something and the event details are clear.")
def calendar_create_event(
    summary: str,
    start_iso: str,
    end_iso: str = "",
    duration_minutes: int = 30,
    description: str = "",
    location: str = "",
    attendees_csv: str = "",
    time_zone: str = "",
) -> str:
    title = summary.strip()
    if not title:
        return _tool_payload_with_error(
            "calendar_create_event",
            "calendar_context",
            [],
            "calendar_create_event: could not create the event.",
            error_code="INVALID_INPUT",
            detail="summary is required to create a calendar event",
            message="I need an event title before I can create a calendar event.",
        )

    try:
        start = _parse_event_datetime(start_iso, time_zone=time_zone)
        if end_iso.strip():
            end = _parse_event_datetime(end_iso, time_zone=time_zone)
        else:
            safe_duration = max(15, min(duration_minutes, 8 * 60))
            end = start + timedelta(minutes=safe_duration)
    except ValueError as exc:
        detail = str(exc)
        return _tool_payload_with_error(
            "calendar_create_event",
            "calendar_context",
            [],
            "calendar_create_event: could not create the event.",
            error_code="INVALID_INPUT",
            detail=detail,
            message=detail,
        )

    if end <= start:
        detail = "end time must be after start time"
        return _tool_payload_with_error(
            "calendar_create_event",
            "calendar_context",
            [],
            "calendar_create_event: could not create the event.",
            error_code="INVALID_INPUT",
            detail=detail,
            message=detail,
        )

    payload: dict[str, Any] = {
        "summary": title,
        "start": _calendar_event_time_payload(start, time_zone=time_zone),
        "end": _calendar_event_time_payload(end, time_zone=time_zone),
    }
    if description.strip():
        payload["description"] = description.strip()
    if location.strip():
        payload["location"] = location.strip()
    attendees = [
        {"email": email.strip()}
        for email in attendees_csv.split(",")
        if email.strip()
    ]
    if attendees:
        payload["attendees"] = attendees

    response, error_info = _call_workspace_api(
        "calendar",
        method="POST",
        path="/calendar/v3/calendars/primary/events",
        payload=payload,
    )
    items = [] if error_info else _format_calendar_write_result(response)
    note = error_info.get("detail") or _note("calendar_create_event", "created calendar event", len(items))
    return _tool_payload_with_error(
        "calendar_create_event",
        "calendar_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("drive_list_files", description="Search Google Drive for candidate files, documents, and spreadsheets. Use this first when you need a Google file ID.")
def drive_list_files(query: str = "", max_results: int = 8, mime_type: str = "") -> str:
    filters = ["trashed = false"]
    if query.strip():
        escaped = query.strip().replace("'", "\\'")
        filters.append(f"fullText contains '{escaped}'")
    if mime_type.strip():
        escaped_mime = mime_type.strip().replace("'", "\\'")
        filters.append(f"mimeType = '{escaped_mime}'")
    response, error_info = _call_workspace_api(
        "drive",
        method="GET",
        path=_build_path(
            "/drive/v3/files",
            pageSize=max(1, min(max_results, 10)),
            q=" and ".join(filters),
            fields="files(id,name,mimeType,modifiedTime,webViewLink),nextPageToken",
        ),
    )
    items = _format_drive_files(response)
    note = error_info.get("detail") or _note("drive_list_files", "searched Drive", len(items))
    return _tool_payload_with_error(
        "drive_list_files",
        "drive_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("docs_get_document", description="Read the contents of a Google Doc by document ID. Use after finding the document ID via Drive or user input.")
def docs_get_document(document_id: str) -> str:
    response, error_info = _call_workspace_api(
        "docs",
        method="GET",
        path=f"/v1/documents/{quote(document_id.strip(), safe='')}",
    )
    items = _format_document(response)
    note = error_info.get("detail") or _note("docs_get_document", "read Google Doc", len(items))
    return _tool_payload_with_error(
        "docs_get_document",
        "docs_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("sheets_get_spreadsheet", description="Read spreadsheet metadata and sheet names by spreadsheet ID. Use to understand workbook structure before reading a range.")
def sheets_get_spreadsheet(spreadsheet_id: str) -> str:
    response, error_info = _call_workspace_api(
        "sheets",
        method="GET",
        path=_build_path(
            f"/v4/spreadsheets/{quote(spreadsheet_id.strip(), safe='')}",
            fields="spreadsheetId,properties.title,sheets.properties",
        ),
    )
    items = _format_spreadsheet(response)
    note = error_info.get("detail") or _note("sheets_get_spreadsheet", "read spreadsheet metadata", len(items))
    return _tool_payload_with_error(
        "sheets_get_spreadsheet",
        "sheets_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("sheets_read_range", description="Read a specific A1 range from a Google Sheet. Use after identifying the spreadsheet and the range you need.")
def sheets_read_range(spreadsheet_id: str, range_a1: str) -> str:
    encoded_range = quote(range_a1.strip(), safe="!:$,')(")
    response, error_info = _call_workspace_api(
        "sheets",
        method="GET",
        path=f"/v4/spreadsheets/{quote(spreadsheet_id.strip(), safe='')}/values/{encoded_range}",
    )
    items = _format_sheet_values(response)
    note = error_info.get("detail") or _note("sheets_read_range", "read sheet range", max(len(items) - 1, 0))
    return _tool_payload_with_error(
        "sheets_read_range",
        "sheets_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("tasks_list_tasklists", description="List Google Task lists. Use before reading tasks when you do not yet know which task list matters.")
def tasks_list_tasklists(max_results: int = 10) -> str:
    response, error_info = _call_workspace_api(
        "tasks",
        method="GET",
        path=_build_path("/tasks/v1/users/@me/lists", maxResults=max(1, min(max_results, 20))),
    )
    items = _format_tasklists(response)
    note = error_info.get("detail") or _note("tasks_list_tasklists", "listed task lists", len(items))
    return _tool_payload_with_error(
        "tasks_list_tasklists",
        "tasks_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("tasks_list_tasks", description="List tasks from a Google Task list. Use @default for the default list when no specific list ID is known.")
def tasks_list_tasks(tasklist_id: str = "@default", max_results: int = 10, show_completed: bool = False) -> str:
    response, error_info = _call_workspace_api(
        "tasks",
        method="GET",
        path=_build_path(
            f"/tasks/v1/lists/{quote(tasklist_id.strip() or '@default', safe='@')}/tasks",
            maxResults=max(1, min(max_results, 20)),
            showCompleted=str(show_completed).lower(),
        ),
    )
    items = _format_tasks(response)
    note = error_info.get("detail") or _note("tasks_list_tasks", "listed tasks", len(items))
    return _tool_payload_with_error(
        "tasks_list_tasks",
        "tasks_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


@tool("keep_list_notes", description="List Google Keep notes. Use for note, reminder, and scratchpad questions.")
def keep_list_notes(filter_query: str = "", page_size: int = 10) -> str:
    response, error_info = _call_workspace_api(
        "keep",
        method="GET",
        path=_build_path("/v1/notes", pageSize=max(1, min(page_size, 20)), filter=filter_query),
    )
    items = _format_keep_notes(response)
    note = error_info.get("detail") or _note("keep_list_notes", "listed Keep notes", len(items))
    return _tool_payload_with_error(
        "keep_list_notes",
        "keep_context",
        items,
        note,
        error_code=error_info.get("code", ""),
        authorization_url=error_info.get("authorization_url", ""),
        detail=error_info.get("detail", ""),
        message=error_info.get("message", ""),
    )


WORKSPACE_TOOLS = [
    gmail_list_messages,
    gmail_get_message,
    calendar_list_events,
    calendar_create_event,
    drive_list_files,
    docs_get_document,
    sheets_get_spreadsheet,
    sheets_read_range,
    tasks_list_tasklists,
    tasks_list_tasks,
    keep_list_notes,
]
TOOL_NODE = ToolNode(WORKSPACE_TOOLS)
AGENT_LLM = llm.bind_tools(WORKSPACE_TOOLS)


def ingest_request(state: WorkspaceState) -> dict[str, Any]:
    message = ""
    if state.get("messages"):
        message = _message_text(state["messages"][-1])
    objective, context = _parse_request(message)

    evidence = [f"Workspace objective: {objective}"]
    for context_key, items in context.items():
        if items:
            evidence.append(f"Seeded {len(items)} item(s) for {context_key} from the request.")

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


def _merge_context_items(existing: list[str], new_items: list[str]) -> list[str]:
    merged = list(existing)
    seen = set(existing)
    for item in new_items:
        if item not in seen:
            merged.append(item)
            seen.add(item)
    return merged[: MAX_LIST_ITEMS * 2]


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
            current_items = context.get(context_key, [])
            new_items = [str(item).strip() for item in items if str(item).strip()]
            context[context_key] = _merge_context_items(current_items, new_items)
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


def _extract_rate_limit_directive(messages: list[AnyMessage]) -> dict[str, str]:
    rate_limited: dict[str, str] = {}

    for message in messages:
        try:
            payload = json.loads(_message_text(message))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue

        error_code = str(payload.get("error_code") or "").strip()
        if not error_code and str(payload.get("error") or "").strip().startswith("HTTP 429"):
            error_code = "HTTP_429"
        if not error_code and str(payload.get("code") or "").strip() in {"HTTP_429", "RATE_LIMITED"}:
            error_code = "HTTP_429"

        if error_code == "HTTP_429" and not rate_limited:
            rate_limited = {
                "code": "RATE_LIMITED",
                "tool": str(payload.get("tool") or "").strip(),
                "message": str(
                    payload.get("message")
                    or payload.get("detail")
                    or "Google temporarily rate limited that request. Please wait a minute and try again."
                ).strip(),
            }

    return rate_limited


def handler(request: dict[str, Any], context: Any = None) -> dict[str, Any]:
    try:
        messages = [HumanMessage(content=str(request.get("message") or ""))]
    except Exception:
        messages = [{"role": "user", "content": str(request.get("message") or "")}]

    result = graph.invoke({"messages": messages})
    directive = _extract_rate_limit_directive(result.get("messages", []))
    if directive.get("code") == "RATE_LIMITED":
        message = directive.get("message") or "Google temporarily rate limited that request. Please wait a minute and try again."
        return {
            "code": "RATE_LIMITED",
            "message": message,
            "response": message,
        }

    messages = result.get("messages", [])
    if messages:
        return {"response": _message_text(messages[-1])}
    return {"response": str(result)}


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
