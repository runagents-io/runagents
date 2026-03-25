"""Expense review starter for RunAgents catalog."""

from typing import Any, Dict


def handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    report = payload.get("expense_report", {})
    amount = report.get("amount", "unknown")
    employee = report.get("employee", "employee")
    return {
        "summary": f"Prepared finance review packet for {employee}.",
        "status": "needs_approval",
        "highlights": [f"Expense amount: {amount}", "Attach policy context from ERP and expense system before approval."],
    }
