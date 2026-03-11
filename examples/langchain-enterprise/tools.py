"""
tools.py — LangChain tool definitions for the HR assistant.

Three tools with different RunAgents policy behaviours:

  hr-knowledge-base   → Open access (auto-PolicyBinding, no approval)
  employee-directory  → Restricted (explicit PolicyBinding required)
  compensation-api    → Restricted + requireApproval (JIT approval on each call)

KEY DESIGN: Tools use plain requests.post() / requests.get().
The Istio sidecar intercepts every outbound call BEFORE it leaves the pod:
  1. Identifies the target Tool CRD by matching the destination hostname
  2. Checks the agent's PolicyBinding for that tool
  3. If requireApproval: true → returns 403 APPROVAL_REQUIRED instead of forwarding
  4. If allowed → injects Authorization + X-End-User-ID headers and forwards

Your tool code never manages API keys, tokens, or access control.
You only handle the 403 APPROVAL_REQUIRED response.

IDENTITY: Every tool call receives the X-End-User-ID header automatically.
The mesh forwards it from the agent's incoming request to every outbound call.
You can also set it explicitly (shown below) for clarity and testability.
"""

import json
import os
import requests
from contextvars import ContextVar
from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Tool base URLs — injected by the operator at deploy time.
# Locally: set TOOL_URL_* env vars or let `runagents dev` set them.
# ---------------------------------------------------------------------------
KNOWLEDGE_BASE_URL  = os.environ.get("TOOL_URL_HR_KNOWLEDGE_BASE",  "http://localhost:9090")
EMPLOYEE_DIR_URL    = os.environ.get("TOOL_URL_EMPLOYEE_DIRECTORY",  "http://localhost:9090")
COMPENSATION_URL    = os.environ.get("TOOL_URL_COMPENSATION_API",    "http://localhost:9090")

# ---------------------------------------------------------------------------
# Identity context — set once per request by the handler in agent.py.
# Every tool call reads from this to propagate X-End-User-ID.
#
# The platform mesh forwards this header automatically, but setting it
# explicitly in requests makes identity flow visible in code and testable
# without a full platform deployment.
# ---------------------------------------------------------------------------
_current_user: ContextVar[str] = ContextVar("current_user", default="")


def set_user_context(user_id: str) -> None:
    """Call this at the start of each handler invocation."""
    _current_user.set(user_id)


def _identity_headers() -> dict:
    """Build request headers including the verified end-user identity."""
    headers = {"Content-Type": "application/json"}
    user_id = _current_user.get()
    if user_id:
        # The mesh already forwards X-End-User-ID automatically, but setting it
        # here ensures it's included even in local development without the mesh.
        headers["X-End-User-ID"] = user_id
    return headers


# ---------------------------------------------------------------------------
# Tool 1: HR Knowledge Base
#
# Access: Open
# PolicyBinding: Auto-created by the agent operator (requireApproval: false)
# Behaviour: Works immediately, no configuration needed.
#
# This is the simplest case — any agent with hr-knowledge-base in its
# requiredTools list gets an automatic PolicyBinding. The mesh forwards
# the call with the configured API key injected (auth_type: None here
# means no credential injection, but the mesh still enforces policy).
# ---------------------------------------------------------------------------

@tool
def search_knowledge_base(query: str) -> str:
    """Search the HR policy and procedures knowledge base.

    Use this for questions about company policies, procedures, benefits,
    leave entitlements, and compliance requirements.

    Args:
        query: Natural language search query
    """
    try:
        resp = requests.get(
            f"{KNOWLEDGE_BASE_URL}/articles/search",
            params={"q": query, "limit": 3},
            headers=_identity_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results.get("articles"):
            return "No articles found for that query."
        return json.dumps(results["articles"], indent=2)
    except requests.HTTPError as e:
        return f"Knowledge base error: {e.response.status_code}"
    except requests.ConnectionError:
        return "Knowledge base is unavailable."


# ---------------------------------------------------------------------------
# Tool 2: Employee Directory
#
# Access: Restricted
# PolicyBinding: Must be applied manually (see policy/employee-directory-binding.yaml)
# Behaviour: Returns 403 "operation denied" until PolicyBinding exists.
#            Once the binding exists, works for all calls from this agent.
#
# The Tool CRD has auth_type: APIKey — the mesh injects the API key secret
# into the Authorization header. Your code never sees the key.
# ---------------------------------------------------------------------------

@tool
def get_employee(employee_id: str) -> str:
    """Look up an employee by ID. Returns name, department, role, and manager.

    Requires: employee-directory PolicyBinding for this agent's ServiceAccount.

    Args:
        employee_id: Employee ID (e.g., EMP-042)
    """
    try:
        resp = requests.get(
            f"{EMPLOYEE_DIR_URL}/employees/{employee_id}",
            headers=_identity_headers(),
            timeout=10,
        )

        if resp.status_code == 403:
            data = _safe_json(resp)
            code = data.get("code", "")

            # APPROVAL_REQUIRED: policy allows the call but first requires an
            # admin to approve an AccessRequest for this operation.
            if code == "APPROVAL_REQUIRED":
                _raise_approval_required(resp.url, data)

            # Plain deny: no PolicyBinding exists yet.
            return (
                "Access denied to employee-directory. "
                "Apply policy/employee-directory-binding.yaml and retry."
            )

        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)

    except requests.HTTPError as e:
        return f"Employee directory error: {e.response.status_code}"
    except requests.ConnectionError:
        return "Employee directory is unavailable."


# ---------------------------------------------------------------------------
# Tool 3: Compensation API
#
# Access: Restricted + requireApproval: true (in PolicyBinding)
# PolicyBinding: Must be applied manually (see policy/compensation-binding.yaml)
#                The binding has requireApproval: true, so EVERY call triggers
#                an AccessRequest the first time.
#
# Behaviour on first call:
#   1. ext-authz sees requireApproval: true
#   2. Creates AccessRequest in governance (status: Pending)
#   3. Returns 403 {"code": "APPROVAL_REQUIRED", "action_id": "act-xxx", "run_id": "run-xxx"}
#   4. This function raises ApprovalRequired
#   5. handler() in agent.py catches it and returns a "pending approval" response
#   6. The run pauses (PAUSED_APPROVAL)
#
# Behaviour after approval:
#   7. Admin approves in console: runagents approvals approve act-xxx
#   8. ResumeWorker polls approved actions
#   9. Calls POST /resume/act-xxx on the agent pod
#  10. Runtime restores checkpoint (conversation history + pending calls)
#  11. Re-executes this tool call — NOW the call goes through (approved)
#  12. Agent continues and completes
#
# NOTE: The Tool CRD has auth_type: OAuth2 — the mesh injects a per-user
# OAuth2 access token retrieved from governance. The compensation system
# receives both the user's identity AND their delegated OAuth2 token.
# Your code never touches tokens.
# ---------------------------------------------------------------------------

# Import ApprovalRequired from the runtime — same exception the platform raises
from runagents.runtime import ApprovalRequired


def _raise_approval_required(url: str, data: dict) -> None:
    """Raise ApprovalRequired so the handler can return a paused response.

    This is the same exception the platform runtime raises internally.
    By raising it here (in a Tier 2 LangChain agent), we plug into the
    same approval/resume machinery.
    """
    raise ApprovalRequired(url, data)


@tool
def update_compensation(employee_id: str, new_salary: float, reason: str = "") -> str:
    """Update an employee's base salary. REQUIRES ADMIN APPROVAL.

    This operation triggers a just-in-time approval request. Execution
    will pause until an HR manager approves the request in the console.

    Args:
        employee_id: Employee ID (e.g., EMP-042)
        new_salary:  New annual base salary in USD
        reason:      Business justification for the change
    """
    payload = {
        "employee_id": employee_id,
        "salary": new_salary,
        "reason": reason,
        "requested_by": _current_user.get(),  # audited on the compensation system
    }
    try:
        resp = requests.post(
            f"{COMPENSATION_URL}/compensation/{employee_id}",
            json=payload,
            headers=_identity_headers(),
            timeout=10,
        )

        if resp.status_code == 403:
            data = _safe_json(resp)
            code = data.get("code", "")

            # APPROVAL_REQUIRED — ext-authz created an AccessRequest.
            # Raise ApprovalRequired so the handler catches it and returns
            # a "pending approval" response. The runtime checkpoints the
            # conversation and the ResumeWorker will resume after approval.
            if code == "APPROVAL_REQUIRED":
                _raise_approval_required(resp.url, data)

            return f"Access denied: no PolicyBinding for compensation-api."

        resp.raise_for_status()
        result = resp.json()
        return (
            f"Compensation updated: {employee_id} → ${new_salary:,.0f}/yr. "
            f"Effective: {result.get('effective_date', 'next pay cycle')}."
        )

    except requests.HTTPError as e:
        return f"Compensation API error: {e.response.status_code}"
    except requests.ConnectionError:
        return "Compensation API is unavailable."


def _safe_json(resp: requests.Response) -> dict:
    try:
        return resp.json()
    except (ValueError, requests.JSONDecodeError):
        return {}


# ---------------------------------------------------------------------------
# All tools — import this list in agent.py
# ---------------------------------------------------------------------------
ALL_TOOLS = [search_knowledge_base, get_employee, update_compensation]
