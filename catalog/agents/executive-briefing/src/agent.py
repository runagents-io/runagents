"""Executive briefing starter for RunAgents catalog."""

from typing import Any, Dict, List


def _collect_titles(items: List[Dict[str, Any]], field: str) -> List[str]:
    titles: List[str] = []
    for item in items[:5]:
        value = str(item.get(field, "")).strip()
        if value:
            titles.append(value)
    return titles


def handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    meetings = payload.get("meetings", []) or []
    project_updates = payload.get("project_updates", []) or []
    stakeholder_notes = payload.get("stakeholder_notes", []) or []

    risks = [item for item in project_updates if str(item.get("status", "")).lower() in {"at_risk", "blocked"}]
    decisions = _collect_titles(project_updates, "decision")
    stakeholder_signals = _collect_titles(stakeholder_notes, "signal")

    return {
        "headline": "Prepared executive daily briefing.",
        "today": _collect_titles(meetings, "title"),
        "top_risks": _collect_titles(risks, "title"),
        "decisions_needed": decisions,
        "stakeholder_signals": stakeholder_signals,
        "recommended_next_step": "Review top risks and decisions before the leadership stand-up.",
    }
