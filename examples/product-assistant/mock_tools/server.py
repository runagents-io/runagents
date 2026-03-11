"""
mock_tools/server.py — Local mock API server for development.

Simulates the three external APIs the agent calls:
  GET  /products/{id}    → product catalog
  GET  /inventory/{sku}  → inventory levels
  POST /pricing/quote    → pricing with discounts
  GET  /healthz          → health check

Stdlib only — no dependencies required.

Usage:
    python mock_tools/server.py
    python mock_tools/server.py --port 9091   # custom port

The `runagents dev` command automatically starts this server and points
all TOOL_URL_* env vars at it.
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from mock_tools.data import PRODUCTS, INVENTORY, apply_discount

PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9090


class MockAPIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path

        # GET /healthz
        if path == "/healthz":
            self._json({"status": "ok", "service": "mock-tools"})
            return

        # GET /products/{id}
        if path.startswith("/products/"):
            product_id = path.split("/products/", 1)[1].rstrip("/")
            product = PRODUCTS.get(product_id) or PRODUCTS.get(product_id.upper())
            if product:
                self._json(product)
            else:
                self._json(
                    {"error": f"Product '{product_id}' not found",
                     "available_ids": list(PRODUCTS.keys())},
                    status=404,
                )
            return

        # GET /inventory/{sku}
        if path.startswith("/inventory/"):
            sku = path.split("/inventory/", 1)[1].rstrip("/")
            stock = INVENTORY.get(sku) or INVENTORY.get(sku.upper())
            if stock:
                self._json(stock)
            else:
                self._json(
                    {"error": f"SKU '{sku}' not found in inventory",
                     "available_skus": list(INVENTORY.keys())},
                    status=404,
                )
            return

        self._json({"error": f"Unknown GET endpoint: {path}"}, status=404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        # POST /pricing/quote
        if path == "/pricing/quote":
            sku = body.get("sku", "")
            quantity = int(body.get("quantity", 1))
            promo_code = body.get("promo_code", "")

            if not sku:
                self._json({"error": "sku is required"}, status=400)
                return

            product = PRODUCTS.get(sku) or PRODUCTS.get(sku.upper())
            if not product:
                self._json({"error": f"SKU '{sku}' not found"}, status=404)
                return

            result = apply_discount(product, quantity, promo_code)
            self._json(result)
            return

        self._json({"error": f"Unknown POST endpoint: {path}"}, status=404)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # Cleaner log format
        print(f"  {self.command:<6} {self.path}  →  {args[1]}")


def main():
    print(f"Mock tool server running on http://localhost:{PORT}")
    print(f"  GET  /products/{{id}}   → product details")
    print(f"  GET  /inventory/{{sku}} → stock levels")
    print(f"  POST /pricing/quote    → price + discounts")
    print(f"  GET  /healthz          → health check")
    print(f"\nPress Ctrl+C to stop.\n")

    server = HTTPServer(("0.0.0.0", PORT), MockAPIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMock server stopped.")


if __name__ == "__main__":
    main()
