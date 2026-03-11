"""
invoke.py — Test and monitor the deployed product-assistant agent.

Demonstrates:
  - Invoking the agent with a message
  - Streaming SSE events
  - Listing runs and viewing event timelines
  - Checking for pending approvals

Usage:
    python invoke.py                      # sync invoke, default message
    python invoke.py "your message here"  # custom message
    python invoke.py --stream "message"   # SSE streaming
    python invoke.py --runs               # list recent runs
    python invoke.py --approvals          # list pending approvals
"""

import json
import sys
import time
import urllib.request
import urllib.error

from runagents import Client
from runagents.config import load_config

AGENT_NAME = "product-assistant"
NAMESPACE = "default"

# Sample messages to try
SAMPLE_MESSAGES = [
    "What wireless headphones do you have?",
    "Is PRD-001 in stock? How much for 10 units?",
    "Apply promo code SAVE20 to 25 units of PRD-002",
    "Compare pricing for 5, 10, and 50 units of SKU-003",
]


def invoke_sync(message: str, client: Client, cfg) -> str:
    """Invoke the agent and wait for the full response."""
    ns = cfg.namespace or NAMESPACE
    endpoint = cfg.endpoint.rstrip("/")
    url = f"{endpoint}/api/agents/{ns}/{AGENT_NAME}/invoke"

    data = json.dumps({"message": message}).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg.api_key}",
        "X-Workspace-Namespace": ns,
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result.get("response") or result.get("message") or json.dumps(result)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "PAUSED_APPROVAL" in body or "APPROVAL_REQUIRED" in body:
            print("\n⏸  Run paused — approval required.")
            print("   Run `python invoke.py --approvals` to see pending requests.")
            try:
                detail = json.loads(body)
                print(f"   Action ID: {detail.get('action_id', 'N/A')}")
                print(f"   Run ID:    {detail.get('run_id', 'N/A')}")
            except Exception:
                pass
            return ""
        raise


def invoke_stream(message: str, cfg) -> None:
    """Invoke with SSE streaming — prints events as they arrive."""
    ns = cfg.namespace or NAMESPACE
    endpoint = cfg.endpoint.rstrip("/")
    url = f"{endpoint}/api/agents/{ns}/{AGENT_NAME}/invoke/stream"

    data = json.dumps({"message": message}).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg.api_key}",
        "X-Workspace-Namespace": ns,
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    print(f"Streaming response for: {message!r}\n")

    with urllib.request.urlopen(req, timeout=120) as resp:
        for raw_line in resp:
            line = raw_line.decode().strip()
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                print("\n[stream complete]")
                break
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type", "")
            if event_type == "tool_call":
                tool = event.get("tool", "")
                inp = json.dumps(event.get("input", {}), separators=(",", ":"))
                print(f"  🔧 tool_call  {tool}({inp})")
            elif event_type == "tool_result":
                tool = event.get("tool", "")
                out = json.dumps(event.get("output", {}), separators=(",", ":"))
                # Truncate long results for readability
                if len(out) > 120:
                    out = out[:120] + "..."
                print(f"  ✓  result    {tool} → {out}")
            elif event_type == "content":
                delta = event.get("delta", "")
                print(delta, end="", flush=True)
            elif event_type == "done":
                print()


def list_runs(client: Client, cfg) -> None:
    """List recent runs and show their event timelines."""
    ns = cfg.namespace or NAMESPACE
    runs = client.runs.list(agent=AGENT_NAME, limit=5)

    if not runs:
        print(f"No runs found for agent '{AGENT_NAME}'.")
        print("Invoke the agent first: python invoke.py")
        return

    print(f"Recent runs for '{AGENT_NAME}' (namespace: {ns}):\n")
    for run in runs:
        status_icon = {
            "COMPLETED": "✓",
            "FAILED": "✗",
            "RUNNING": "⟳",
            "PAUSED_APPROVAL": "⏸",
        }.get(run.status, "?")

        print(f"  {status_icon} {run.id}  {run.status}  {run.created_at}")

        # Show event timeline for the first run
        if run == runs[0]:
            events = client.runs.events(run.id)
            if events:
                print(f"\n    Event timeline ({len(events)} events):")
                for event in events:
                    print(f"      [{event.sequence:02d}] {event.type:<20} {json.dumps(event.data)[:80]}")
        print()


def list_approvals(client: Client) -> None:
    """List pending approval requests."""
    approvals = client.approvals.list()

    if not approvals:
        print("No pending approval requests.")
        print()
        print("To require approvals for the pricing-engine tool:")
        print("  1. Go to Tools → pricing-engine → Edit in the console")
        print("  2. Set Access Mode to 'Critical'")
        print("  3. Re-invoke the agent with a pricing request")
        return

    print(f"Pending approvals ({len(approvals)}):\n")
    for req in approvals:
        req_id = req.get("id", "?")
        tool = req.get("tool", "?")
        agent = req.get("agent", "?")
        created = req.get("created_at", "?")
        print(f"  ID:      {req_id}")
        print(f"  Tool:    {tool}")
        print(f"  Agent:   {agent}")
        print(f"  Created: {created}")
        print()

    if approvals:
        req_id = approvals[0].get("id")
        print(f"Approve the first one:")
        print(f"  python invoke.py --approve {req_id}")
        print(f"  # or via CLI: runagents approvals approve {req_id}")


def approve_request(request_id: str, client: Client) -> None:
    """Approve a pending access request."""
    print(f"Approving request {request_id}...")
    result = client.approvals.approve(request_id)
    if isinstance(result, dict) and result.get("error"):
        print(f"Error: {result['error']}")
    else:
        print(f"Approved ✓")
        print("The paused run will resume automatically within ~10 seconds.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    args = sys.argv[1:]
    cfg = load_config()

    if not cfg.endpoint or cfg.endpoint == "http://localhost:8092":
        print("Error: platform endpoint not configured.")
        print("Run: runagents config set endpoint https://<your-id>.try.runagents.io")
        sys.exit(1)

    if not cfg.api_key:
        print("Error: API key not configured.")
        print("Run: runagents config set api-key ra_ws_YOUR_KEY_HERE")
        sys.exit(1)

    client = Client()

    # --runs: list recent runs
    if args and args[0] == "--runs":
        list_runs(client, cfg)
        return

    # --approvals: list pending approvals
    if args and args[0] == "--approvals":
        list_approvals(client)
        return

    # --approve <id>: approve a request
    if len(args) >= 2 and args[0] == "--approve":
        approve_request(args[1], client)
        return

    # --stream <message>: streaming invoke
    if args and args[0] == "--stream":
        message = " ".join(args[1:]) if len(args) > 1 else SAMPLE_MESSAGES[1]
        invoke_stream(message, cfg)
        return

    # Default: sync invoke
    message = " ".join(args) if args else SAMPLE_MESSAGES[0]

    print(f"Invoking '{AGENT_NAME}'...")
    print(f"User: {message}")
    print("-" * 60)

    start = time.time()
    response = invoke_sync(message, client, cfg)
    elapsed = time.time() - start

    if response:
        print(f"Agent: {response}")
        print()
        print(f"({elapsed:.1f}s)")
        print()
        print("Next steps:")
        print("  python invoke.py --runs               # see run timeline")
        print("  python invoke.py --stream 'message'   # streaming mode")
        print("  python invoke.py --approvals          # pending approvals")


if __name__ == "__main__":
    main()
