"""HR policy helper starter for RunAgents catalog."""

from typing import Any, Dict

SENSITIVE_TOPICS = {"termination", "investigation", "legal"}


def handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    question = str(payload.get("question", ""))
    lowered = question.lower()
    escalate = any(topic in lowered for topic in SENSITIVE_TOPICS)
    return {
        "answer": "Drafted a grounded HR policy response.",
        "requires_escalation": escalate,
        "next_step": "Route to HR specialist" if escalate else "Answer employee with cited policy",
    }
