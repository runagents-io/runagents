"""
LangChain tools — call external APIs via HTTP.

Tool URLs come from environment variables with a localhost fallback:
  - Locally: mock_server.py handles all three on :9090
  - On RunAgents: TOOL_URL_* is injected by the operator per tool CRD

No platform-specific code here. This is standard LangChain.
"""

import json
import os
import requests
from langchain_core.tools import tool

FAQ_URL     = os.environ.get("TOOL_URL_FAQ_SERVICE",     "http://localhost:9090")
ACCOUNT_URL = os.environ.get("TOOL_URL_ACCOUNT_SERVICE", "http://localhost:9090")
TICKET_URL  = os.environ.get("TOOL_URL_TICKET_SERVICE",  "http://localhost:9090")


@tool
def search_faq(query: str) -> str:
    """Search the FAQ and knowledge base. Use for policy, product, shipping, and returns questions."""
    try:
        resp = requests.get(f"{FAQ_URL}/faq/search", params={"q": query}, timeout=5)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return "No FAQ entries found for that query."
        return "\n\n".join(f"Q: {r['question']}\nA: {r['answer']}" for r in results[:2])
    except requests.ConnectionError:
        return "FAQ service unavailable. Start mock_server.py for local testing."


@tool
def lookup_account(customer_id: str) -> str:
    """Look up a customer account by ID. Returns plan, status, and billing info."""
    try:
        resp = requests.get(f"{ACCOUNT_URL}/accounts/{customer_id}", timeout=5)
        if resp.status_code == 404:
            return f"No account found for ID: {customer_id}"
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except requests.ConnectionError:
        return "Account service unavailable. Start mock_server.py for local testing."


@tool
def update_account_plan(customer_id: str, new_plan: str) -> str:
    """Update a customer's subscription plan. Plans: free, starter, pro, enterprise."""
    try:
        resp = requests.post(
            f"{ACCOUNT_URL}/accounts/{customer_id}/plan",
            json={"plan": new_plan},
            timeout=5,
        )
        resp.raise_for_status()
        return f"Plan updated to '{new_plan}' for customer {customer_id}."
    except requests.ConnectionError:
        return "Account service unavailable."


@tool
def create_support_ticket(customer_id: str, category: str, summary: str, priority: str = "normal") -> str:
    """Create a support ticket for issues needing human follow-up.
    Categories: billing, technical, account, general. Priority: low, normal, high, urgent."""
    try:
        resp = requests.post(
            f"{TICKET_URL}/tickets",
            json={"customer_id": customer_id, "category": category, "summary": summary, "priority": priority},
            timeout=5,
        )
        resp.raise_for_status()
        t = resp.json()
        return f"Ticket #{t['id']} created (priority: {t['priority']}). Reference: {t['reference']}"
    except requests.ConnectionError:
        return "Ticket service unavailable."
