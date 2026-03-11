"""
mock_tools/server.py — Local mock HR API server.

Shows identity propagation in action: every request logs the
X-End-User-ID header it receives, demonstrating that the user's
identity flows end-to-end from the JWT to the tool.

In production, X-End-User-ID is injected by the Istio mesh (from the
JWT validated at ingress). Locally, tools.py sets it explicitly from
the request context.

Usage:
    python mock_tools/server.py

Endpoints:
    GET  /articles/search?q=...     → knowledge base articles
    GET  /employees/{id}            → employee record
    POST /compensation/{id}         → update compensation
    GET  /healthz                   → health check

Approval simulation:
    Pass header X-Simulate-Approval: true to simulate a 403 APPROVAL_REQUIRED
    response on compensation calls (useful for testing the approval flow locally).
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9090

# --- Fake HR data ---

ARTICLES = {
    "pto":         {"id": "A001", "title": "PTO Policy",           "content": "Employees receive 20 days PTO per year, accruing at 1.67 days/month. Unused PTO rolls over up to 5 days."},
    "maternity":   {"id": "A002", "title": "Maternity Leave",       "content": "Primary caregivers receive 16 weeks paid maternity/paternity leave. Secondary caregivers receive 4 weeks."},
    "remote":      {"id": "A003", "title": "Remote Work Policy",    "content": "Employees may work remotely up to 3 days per week with manager approval. Full-remote roles require VP approval."},
    "performance": {"id": "A004", "title": "Performance Review",    "content": "Annual reviews in December. Mid-year check-in in June. Merit increases effective Jan 1."},
    "benefits":    {"id": "A005", "title": "Benefits Overview",     "content": "Medical, dental, vision. 401k with 4% match. FSA/HSA. $1,000/yr learning stipend."},
}

EMPLOYEES = {
    "EMP-001": {"id": "EMP-001", "name": "Alice Chen",   "department": "Engineering",    "role": "Senior Engineer",    "manager": "EMP-010", "salary": 145000},
    "EMP-002": {"id": "EMP-002", "name": "Bob Martinez", "department": "Marketing",      "role": "Marketing Manager",  "manager": "EMP-011", "salary": 105000},
    "EMP-042": {"id": "EMP-042", "name": "Jane Doe",     "department": "Product",        "role": "Product Manager",    "manager": "EMP-012", "salary": 130000},
    "EMP-099": {"id": "EMP-099", "name": "Sam Kim",      "department": "HR",             "role": "HR Business Partner","manager": "EMP-013", "salary": 98000},
}


class MockHRHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)
        user   = self.headers.get("X-End-User-ID", "unknown")

        # GET /healthz
        if path == "/healthz":
            self._json({"status": "ok"})
            return

        # GET /articles/search?q=...
        if path == "/articles/search":
            query   = params.get("q", [""])[0].lower()
            matches = [a for k, a in ARTICLES.items() if query in k or query in a["title"].lower() or query in a["content"].lower()]
            if not matches:
                matches = list(ARTICLES.values())[:2]  # return first 2 as fallback
            self._json({"articles": matches, "requested_by": user})
            return

        # GET /employees/{id}
        if path.startswith("/employees/"):
            emp_id   = path.split("/employees/", 1)[1].rstrip("/")
            employee = EMPLOYEES.get(emp_id)
            if employee:
                # Don't expose salary in directory lookup — that's what compensation-api is for
                safe = {k: v for k, v in employee.items() if k != "salary"}
                self._json({**safe, "requested_by": user})
            else:
                self._json({"error": f"Employee {emp_id!r} not found"}, status=404)
            return

        self._json({"error": f"Unknown GET: {path}"}, status=404)

    def do_POST(self):
        path   = urlparse(self.path).path
        body   = self._read_body()
        user   = self.headers.get("X-End-User-ID", "unknown")
        sim_ap = self.headers.get("X-Simulate-Approval", "").lower() == "true"

        # POST /compensation/{id}
        if path.startswith("/compensation/"):
            emp_id = path.split("/compensation/", 1)[1].rstrip("/")

            # Simulate APPROVAL_REQUIRED (for local testing of the approval flow)
            if sim_ap:
                self._json({
                    "code":      "APPROVAL_REQUIRED",
                    "action_id": "act-local-test-001",
                    "run_id":    "run-local-test-001",
                    "tool":      "compensation-api",
                    "message":   "Approval required (simulated for local testing)",
                }, status=403)
                return

            employee = EMPLOYEES.get(emp_id)
            if not employee:
                self._json({"error": f"Employee {emp_id!r} not found"}, status=404)
                return

            new_salary = body.get("salary", employee["salary"])
            old_salary = employee["salary"]
            EMPLOYEES[emp_id]["salary"] = new_salary  # mutate in-memory

            self._json({
                "employee_id":    emp_id,
                "employee_name":  employee["name"],
                "old_salary":     old_salary,
                "new_salary":     new_salary,
                "effective_date": "next pay cycle",
                "approved_by":    user,          # ← identity propagated to the tool
                "reason":         body.get("reason", ""),
            })
            return

        self._json({"error": f"Unknown POST: {path}"}, status=404)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        user = self.headers.get("X-End-User-ID", "—")
        # Log identity on every request so you can see it flowing through
        print(f"  {self.command:<6} {self.path:<40} user={user}  status={args[1]}")


def main():
    print(f"Mock HR API server on http://localhost:{PORT}")
    print(f"  GET  /articles/search?q=...  → knowledge base")
    print(f"  GET  /employees/{{id}}         → employee record")
    print(f"  POST /compensation/{{id}}      → update salary")
    print(f"  GET  /healthz                → health")
    print()
    print(f"Identity: every request logs the X-End-User-ID header it receives.")
    print(f"          This shows user identity flowing end-to-end from the JWT.")
    print()
    print(f"Approval simulation: add -H 'X-Simulate-Approval: true' to POST /compensation")
    print(f"  to get a 403 APPROVAL_REQUIRED response (tests the approval flow locally).")
    print()
    print(f"Press Ctrl+C to stop.\n")

    server = HTTPServer(("0.0.0.0", PORT), MockHRHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMock server stopped.")


if __name__ == "__main__":
    main()
