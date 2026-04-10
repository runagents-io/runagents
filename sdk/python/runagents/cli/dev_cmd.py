"""``runagents dev`` — local dev server with mock tools and hot reload."""

import json
import os
import signal
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path


def run_dev(args: list[str]) -> None:
    if args and args[0] in ("-h", "--help"):
        print(
            "Usage: runagents dev [options]\n\n"
            "Start local dev server.\n\n"
            "Options:\n"
            "  --port PORT     Agent port (default 8080)\n"
            "  --mock-port PORT  Mock tool server port (default 9090)\n"
            "  --no-mock       Skip mock tool server\n"
            "  --watch         Hot-reload on .py changes (requires watchdog)\n"
        )
        return

    # Parse args
    port = 8080
    mock_port = 9090
    use_mock = True
    watch = False
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--mock-port" and i + 1 < len(args):
            mock_port = int(args[i + 1])
            i += 2
        elif args[i] == "--no-mock":
            use_mock = False
            i += 1
        elif args[i] == "--watch":
            watch = True
            i += 1
        else:
            i += 1

    config = _load_runagents_yaml()
    if config is None:
        print("Error: runagents.yaml not found. Run 'runagents init' first.", file=sys.stderr)
        sys.exit(1)

    # Set env vars matching operator injection
    _setup_env(config, mock_port, use_mock)

    print(f"RunAgents Dev Server")
    print(f"  Agent:       :{port}")
    if use_mock:
        print(f"  Mock tools:  :{mock_port}")
    print(f"  Model:       {os.environ.get('LLM_MODEL', 'gpt-4o-mini')}")
    print(f"  Entry point: {config.get('entry_point', 'agent.py')}")
    print()

    # Start mock tool server
    mock_server = None
    if use_mock:
        mock_server = _start_mock_server(mock_port, config.get("tools", []))

    # Start agent runtime
    try:
        if watch:
            _run_with_watch(port, config)
        else:
            _run_agent(port)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if mock_server:
            mock_server.shutdown()


def _load_runagents_yaml() -> dict | None:
    """Load runagents.yaml from current directory."""
    for name in ("runagents.yaml", "runagents.yml"):
        p = Path.cwd() / name
        if p.exists():
            # Use a simple YAML subset parser (stdlib only)
            return _parse_simple_yaml(p.read_text())
    return None


def _parse_simple_yaml(text: str) -> dict:
    """Parse a simple single-level YAML file (no nested objects beyond one level)."""
    result: dict = {}
    current_key = None
    current_list: list | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item
        if stripped.startswith("- "):
            if current_list is not None:
                current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue

        # Key: value
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")

            # Handle nested keys (one level deep via indentation)
            indent = len(line) - len(line.lstrip())
            if indent > 0 and current_key and isinstance(result.get(current_key), dict):
                result[current_key][key] = val
                continue

            if val == "":
                # Could be a list or nested dict
                # Peek: if next non-empty line starts with "- ", it's a list
                result[key] = {}
                current_key = key
                current_list = None
                continue
            elif val == "[]":
                result[key] = []
                current_key = key
                current_list = result[key]
                continue

            result[key] = val
            current_key = key
            current_list = None

    return result


def _setup_env(config: dict, mock_port: int, use_mock: bool) -> None:
    """Set environment variables matching what the operator would inject."""
    os.environ.setdefault("SYSTEM_PROMPT", config.get("system_prompt", "You are a helpful assistant."))
    os.environ.setdefault("AGENT_NAME", config.get("name", "dev-agent"))

    # LLM config
    model_cfg = config.get("model", {})
    if isinstance(model_cfg, dict):
        model = model_cfg.get("model", "gpt-4o-mini")
    else:
        model = "gpt-4o-mini"
    os.environ.setdefault("LLM_MODEL", model)

    # LLM gateway: if platform configured, use it; else direct OpenAI
    if os.environ.get("RUNAGENTS_ENDPOINT"):
        from runagents.config import load_config
        cfg = load_config()
        os.environ.setdefault("LLM_GATEWAY_URL", f"{cfg.endpoint}/v1/chat/completions")
    elif os.environ.get("OPENAI_API_KEY"):
        os.environ.setdefault("LLM_GATEWAY_URL", "https://api.openai.com/v1/chat/completions")
    else:
        os.environ.setdefault("LLM_GATEWAY_URL", "http://localhost:8092/v1/chat/completions")

    # Tools
    tools = config.get("tools", [])
    if isinstance(tools, list) and use_mock:
        for t in tools:
            if isinstance(t, str):
                env_key = "TOOL_URL_" + t.upper().replace("-", "_")
                os.environ.setdefault(env_key, f"http://localhost:{mock_port}")

    # Tool definitions + routes for runtime
    os.environ.setdefault("TOOL_DEFINITIONS_JSON", "[]")
    os.environ.setdefault("TOOL_ROUTES_JSON", "{}")

    # User entry point
    entry = config.get("entry_point", "agent.py")
    if entry:
        module = entry.removesuffix(".py")
        os.environ.setdefault("USER_ENTRY_POINT", module)

    os.environ.setdefault("PORT", "8080")


def _start_mock_server(port: int, tools: list) -> HTTPServer:
    """Start a mock tool server that returns echo responses."""

    class MockHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self._respond({"method": "GET", "path": self.path, "mock": True})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode() if length else "{}"
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {"raw": body}

            self._respond({
                "method": "POST",
                "path": self.path,
                "received": payload,
                "mock": True,
                "result": f"Mock response for {self.path}",
            })

        def do_PUT(self):
            self.do_POST()

        def do_PATCH(self):
            self.do_POST()

        def do_DELETE(self):
            self._respond({"method": "DELETE", "path": self.path, "mock": True, "deleted": True})

        def _respond(self, data: dict) -> None:
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            print(f"  [mock] {args[0]}")

    server = HTTPServer(("0.0.0.0", port), MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _run_agent(port: int) -> None:
    """Start the agent runtime server."""
    os.environ["PORT"] = str(port)

    # Add cwd to path so user's agent.py is importable
    if str(Path.cwd()) not in sys.path:
        sys.path.insert(0, str(Path.cwd()))

    from runagents.runtime import main as runtime_main
    runtime_main()


def _run_with_watch(port: int, config: dict) -> None:
    """Run with file watching and auto-restart."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("Warning: watchdog not installed. Running without hot-reload.")
        print("Install with: pip install runagents[dev]")
        _run_agent(port)
        return

    import subprocess

    process = None
    lock = threading.Lock()

    def start():
        nonlocal process
        env = os.environ.copy()
        env["PORT"] = str(port)
        process = subprocess.Popen(
            [sys.executable, "-c", "from runagents.runtime import main; main()"],
            env=env,
            cwd=str(Path.cwd()),
        )

    def restart():
        nonlocal process
        with lock:
            if process:
                process.terminate()
                process.wait(timeout=5)
            print("  [dev] Restarting agent...")
            start()

    class ReloadHandler(FileSystemEventHandler):
        def __init__(self):
            self._last = 0

        def on_modified(self, event):
            if not event.src_path.endswith(".py"):
                return
            now = time.time()
            if now - self._last < 1:
                return
            self._last = now
            restart()

    observer = Observer()
    observer.schedule(ReloadHandler(), str(Path.cwd()), recursive=True)
    observer.start()

    start()
    try:
        while True:
            if process and process.poll() is not None:
                break
            time.sleep(0.5)
    finally:
        observer.stop()
        observer.join()
        if process:
            process.terminate()
