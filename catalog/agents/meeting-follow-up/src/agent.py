"""Meeting follow-up starter for RunAgents catalog."""

from typing import Any, Dict, List


def _normalize_items(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for item in items:
        task = str(item.get("task", "")).strip()
        if not task:
            continue
        normalized.append(
            {
                "task": task,
                "owner": str(item.get("owner", "TBD")).strip() or "TBD",
                "due": str(item.get("due", "")).strip() or "Unspecified",
            }
        )
    return normalized


def handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    decisions = [str(item).strip() for item in payload.get("decisions", []) if str(item).strip()]
    action_items = _normalize_items(payload.get("action_items", []) or [])
    meeting_title = str(payload.get("meeting_title", "Team meeting")).strip() or "Team meeting"

    return {
        "subject": f"Follow-up: {meeting_title}",
        "decisions": decisions,
        "action_items": action_items,
        "draft_recap": "Prepared a concise recap with decisions, owners, and next steps.",
    }
