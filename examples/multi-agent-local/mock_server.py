"""
mock_server.py — Local mock API server for all three tools.

Serves FAQ, account, and ticket endpoints on a single port.
Start this before running agent.py locally.

Usage:
    python mock_server.py

Logs X-End-User-ID on every request so you can see identity flowing
through to the tools — same as it would on the platform.
"""

import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 9090

FAQ = [
    {"question": "What is your return policy?",    "answer": "Items can be returned within 30 days of purchase with a receipt. Digital products are non-refundable."},
    {"question": "How long does shipping take?",   "answer": "Standard shipping takes 5-7 business days. Express shipping takes 1-2 business days."},
    {"question": "Do you offer student discounts?","answer": "Yes, students get 20% off with a valid .edu email address. Apply at checkout."},
    {"question": "How do I cancel my subscription?","answer": "Go to Account Settings → Subscription → Cancel. You retain access until the end of the billing period."},
    {"question": "What payment methods do you accept?", "answer": "Visa, Mastercard, Amex, PayPal, and bank transfer for annual plans."},
]

ACCOUNTS = {
    "CUST-001": {"id": "CUST-001", "name": "Alice Chen",   "email": "alice@example.com",  "plan": "pro",     "status": "active",   "next_billing": "2026-04-01"},
    "CUST-002": {"id": "CUST-002", "name": "Bob Martinez", "email": "bob@example.com",    "plan": "starter", "status": "active",   "next_billing": "2026-04-15"},
    "CUST-003": {"id": "CUST-003", "name": "Carol Smith",  "email": "carol@example.com",  "plan": "free",    "status": "active",   "next_billing": None},
}

TICKETS = {}


class MockHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)
        user   = self.headers.get("X-End-User-ID", "—")

        if path == "/healthz":
            self._json({"status": "ok"})
        elif path == "/faq/search":
            q       = params.get("q", [""])[0].lower()
            matches = [f for f in FAQ if any(w in f["question"].lower() or w in f["answer"].lower() for w in q.split())]
            self._json({"results": matches[:2] or FAQ[:1]})
        elif path.startswith("/accounts/"):
            cid     = path.split("/accounts/", 1)[1].rstrip("/")
            account = ACCOUNTS.get(cid)
            if account:
                self._json({**account, "requested_by": user})
            else:
                self._json({"error": f"Account {cid} not found"}, 404)
        else:
            self._json({"error": f"Not found: {path}"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._body()
        user = self.headers.get("X-End-User-ID", "—")

        if path.startswith("/accounts/") and path.endswith("/plan"):
            cid = path.split("/accounts/", 1)[1].split("/plan")[0]
            if cid in ACCOUNTS:
                ACCOUNTS[cid]["plan"] = body.get("plan", ACCOUNTS[cid]["plan"])
                self._json({"updated": True, "customer_id": cid, "plan": ACCOUNTS[cid]["plan"], "changed_by": user})
            else:
                self._json({"error": f"Account {cid} not found"}, 404)
        elif path == "/tickets":
            tid = f"TKT-{str(uuid.uuid4())[:8].upper()}"
            ticket = {
                "id":          tid,
                "reference":   f"SUP-{tid}",
                "customer_id": body.get("customer_id", ""),
                "category":    body.get("category", "general"),
                "summary":     body.get("summary", ""),
                "priority":    body.get("priority", "normal"),
                "created_by":  user,
            }
            TICKETS[tid] = ticket
            self._json(ticket)
        else:
            self._json({"error": f"Not found: {path}"}, 404)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        if n == 0:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except (ValueError, json.JSONDecodeError):
            return {}

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        user = self.headers.get("X-End-User-ID", "—")
        print(f"  {self.command:<6} {self.path:<35} user={user:<20} {args[1]}")


if __name__ == "__main__":
    print(f"Mock server on http://localhost:{PORT}")
    print(f"  GET  /faq/search?q=...        → FAQ search")
    print(f"  GET  /accounts/{{id}}           → account lookup")
    print(f"  POST /accounts/{{id}}/plan      → update plan")
    print(f"  POST /tickets                  → create ticket")
    print(f"\nIdentity: every request logs X-End-User-ID\n")
    try:
        HTTPServer(("0.0.0.0", PORT), MockHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
