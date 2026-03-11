"""
tools.py — HTTP tool wrappers shared across all agents.

Tools call external APIs using requests. The URL comes from an env var
with a local fallback — the same code works locally and on the platform.

LOCAL:  TOOL_URL_* points to mock_server.py on localhost
PLATFORM: TOOL_URL_* is injected by the operator; the Istio mesh
          intercepts every call, checks policy, and injects credentials.
          Your code here does not change between the two environments.
"""

import os
import json
import requests
from langchain_core.tools import tool

# Tool base URLs.
# Locally: mock_server.py runs on :9090 (same URL for all tools).
# On platform: each tool gets its own TOOL_URL_* env var pointing to
# the registered Tool CRD's base URL.
FAQ_URL     = os.environ.get("TOOL_URL_FAQ_SERVICE",     "http://localhost:9090")
ACCOUNT_URL = os.environ.get("TOOL_URL_ACCOUNT_SERVICE", "http://localhost:9090")
TICKET_URL  = os.environ.get("TOOL_URL_TICKET_SERVICE",  "http://localhost:9090")

# The platform injects X-End-User-ID via the Istio mesh automatically.
# We read it here to pass it explicitly — useful for local dev and
# to make identity visible in mock server logs.
_request_user_id = ""

def set_user_id(user_id: str):
    global _request_user_id
    _request_user_id = user_id

def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if _request_user_id:
        h["X-End-User-ID"] = _request_user_id
    return h


# --- FAQ / Knowledge Base ---

@tool
def search_faq(query: str) -> str:
    """Search the FAQ and knowledge base for answers to common questions.
    Use for questions about policies, products, shipping, returns, etc."""
    try:
        resp = requests.get(
            f"{FAQ_URL}/faq/search",
            params={"q": query},
            headers=_headers(),
            timeout=5,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return "No FAQ entries found for that query."
        return "\n\n".join(f"Q: {r['question']}\nA: {r['answer']}" for r in results[:2])
    except requests.ConnectionError:
        return "FAQ service unavailable. Start mock_server.py for local testing."


# --- Account Service ---

@tool
def lookup_account(customer_id: str) -> str:
    """Look up a customer account by ID. Returns account status, plan, and billing info."""
    try:
        resp = requests.get(
            f"{ACCOUNT_URL}/accounts/{customer_id}",
            headers=_headers(),
            timeout=5,
        )
        if resp.status_code == 404:
            return f"No account found for customer ID: {customer_id}"
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
            headers=_headers(),
            timeout=5,
        )
        resp.raise_for_status()
        return f"Plan updated to '{new_plan}' for customer {customer_id}."
    except requests.ConnectionError:
        return "Account service unavailable."


# --- Ticket Service ---

@tool
def create_support_ticket(
    customer_id: str,
    category: str,
    summary: str,
    priority: str = "normal",
) -> str:
    """Create a support ticket for issues that need human follow-up.
    Categories: billing, technical, account, general.
    Priority: low, normal, high, urgent."""
    try:
        resp = requests.post(
            f"{TICKET_URL}/tickets",
            json={
                "customer_id": customer_id,
                "category":    category,
                "summary":     summary,
                "priority":    priority,
            },
            headers=_headers(),
            timeout=5,
        )
        resp.raise_for_status()
        ticket = resp.json()
        return f"Ticket #{ticket['id']} created (priority: {ticket['priority']}). Reference: {ticket['reference']}"
    except requests.ConnectionError:
        return "Ticket service unavailable."
