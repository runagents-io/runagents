"""
RunAgents Agent Runtime — HTTP server that handles /invoke for deployed agents.

Reads environment variables injected by the operator:
  SYSTEM_PROMPT          — agent's system prompt
  LLM_GATEWAY_URL        — full URL to LLM Gateway chat completions endpoint
  LLM_MODEL              — model name (e.g. gpt-4o-mini)
  AGENT_NAME             — name of this agent (for logging)
  TOOL_DEFINITIONS_JSON  — OpenAI-format tool definitions array
  TOOL_ROUTES_JSON       — function name → HTTP route mapping
  MAX_TOOL_ITERATIONS    — max tool calling loop iterations (default 10)
  USER_ENTRY_POINT       — Python module to import as user's agent code (optional)
  RUNAGENTS_USER_CODE_DIR — mounted source tree for shared-runtime execution (optional)

Listens on :8080. Stdlib only — no pip dependencies required.
"""

import asyncio
import contextlib
import contextvars
import importlib
import ipaddress
import inspect
import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

try:
    from langgraph.errors import GraphBubbleUp as _ToolInterruptBase
except Exception:  # pragma: no cover - langgraph is optional for non-graph agents
    _ToolInterruptBase = Exception

# --- Configuration ---

SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant.")
LLM_GATEWAY_URL = os.environ.get("LLM_GATEWAY_URL", "http://llm-gateway.agent-system.svc:8080/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
AGENT_NAME = os.environ.get("AGENT_NAME", "agent")
PORT = int(os.environ.get("PORT", "8080"))
MAX_TOOL_ITERATIONS = int(os.environ.get("MAX_TOOL_ITERATIONS", "10"))
GOVERNANCE_URL = os.environ.get("GOVERNANCE_URL", "http://governance.agent-system.svc:8092")

# Parse tool definitions and routes from env vars
TOOL_DEFINITIONS = []
TOOL_ROUTES = {}
TOOL_URLS = {}
TOOL_URL_PREFIXES = []
TOOL_URL_REWRITES = {}
OUTBOUND_MODE = "direct"

# User handler discovered at startup (Tier 2 agents)
USER_HANDLER = None

_TOOL_TRACE_SESSION = contextvars.ContextVar("runagents_tool_trace_session", default=None)
_SUPPRESS_HTTP_TOOL_TRACE = contextvars.ContextVar("runagents_suppress_http_tool_trace", default=False)
_END_USER_ID = contextvars.ContextVar("runagents_end_user_id", default="")
_ORIGINAL_URLOPEN = urllib.request.urlopen
_REQUESTS_ORIGINAL_SESSION_REQUEST = None
_HTTP_HOOKS_INSTALLED = False


def _init_tools():
    global TOOL_DEFINITIONS, TOOL_ROUTES, TOOL_URLS, TOOL_URL_PREFIXES, OUTBOUND_MODE
    TOOL_DEFINITIONS = []
    TOOL_ROUTES = {}
    TOOL_URLS = {}
    TOOL_URL_PREFIXES = []
    OUTBOUND_MODE = _load_outbound_mode()
    raw_defs = os.environ.get("TOOL_DEFINITIONS_JSON", "")
    if raw_defs:
        try:
            TOOL_DEFINITIONS = json.loads(raw_defs)
        except json.JSONDecodeError:
            _log("warn", "failed to parse TOOL_DEFINITIONS_JSON")

    raw_routes = os.environ.get("TOOL_ROUTES_JSON", "")
    if raw_routes:
        try:
            TOOL_ROUTES = json.loads(raw_routes)
        except json.JSONDecodeError:
            _log("warn", "failed to parse TOOL_ROUTES_JSON")

    # Collect all TOOL_URL_* env vars
    for key, val in os.environ.items():
        if key.startswith("TOOL_URL_"):
            TOOL_URLS[key] = val
    TOOL_URL_PREFIXES = _build_tool_url_prefixes()


def _build_tool_url_prefixes():
    prefixes = []
    for env_key, raw_url in TOOL_URLS.items():
        tool_name = env_key.replace("TOOL_URL_", "").lower().replace("_", "-")
        normalized = (raw_url or "").strip()
        if not normalized:
            continue
        prefixes.append((normalized.rstrip("/"), tool_name))
    prefixes.sort(key=lambda item: len(item[0]), reverse=True)
    return prefixes


def _load_url_rewrites():
    raw = os.environ.get("TOOL_URL_REWRITES_JSON", "")
    if not raw:
        return {}

    try:
        rewrites = json.loads(raw)
    except json.JSONDecodeError:
        _log("warn", "failed to parse TOOL_URL_REWRITES_JSON")
        return {}

    return rewrites if rewrites else {}


def _load_outbound_mode():
    raw = os.environ.get("RUNAGENTS_OUTBOUND_MODE", "direct")
    normalized = str(raw).strip().lower()
    if normalized in ("alias", "strict"):
        return normalized
    return "direct"


def _sorted_rewrite_prefixes():
    return sorted(TOOL_URL_REWRITES.keys(), key=len, reverse=True)


def _rewrite_url(url):
    if not TOOL_URL_REWRITES:
        _enforce_outbound_mode(url, url)
        return url
    for placeholder in _sorted_rewrite_prefixes():
        if url.startswith(placeholder):
            target = TOOL_URL_REWRITES[placeholder]
            suffix = url[len(placeholder):]
            target_path = urllib.parse.urlparse(target).path
            if not suffix:
                _enforce_outbound_mode(url, target)
                return target
            if target_path and target_path != "/" and target_path.endswith(suffix):
                _enforce_outbound_mode(url, target)
                return target
            rewritten = target.rstrip("/") + suffix
            _enforce_outbound_mode(url, rewritten)
            return rewritten
    _enforce_outbound_mode(url, url)
    return url


def _is_private_or_internal_host(hostname):
    host = (hostname or "").strip().lower()
    if not host:
        return True
    if host in ("localhost", "127.0.0.1", "::1"):
        return True
    if host.endswith(".svc") or host.endswith(".svc.cluster.local") or host.endswith(".cluster.local"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def _is_external_http_url(url):
    try:
        parsed = urllib.parse.urlparse(str(url))
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    return not _is_private_or_internal_host(parsed.hostname)


class UnboundOutboundURL(RuntimeError):
    """Raised in strict mode when outbound HTTP(S) is not bound to a managed tool."""

    def __init__(self, url):
        self.url = str(url)
        super().__init__(f"Outbound URL {self.url!r} is not bound to a managed tool")


def _enforce_outbound_mode(original_url, rewritten_url):
    if OUTBOUND_MODE != "strict":
        return
    if str(rewritten_url) != str(original_url):
        return
    if not _is_external_http_url(original_url):
        return
    raise UnboundOutboundURL(original_url)


def _infer_tool_name_from_url(url):
    candidate = (url or "").strip()
    if not candidate:
        return ""
    for prefix, tool_name in TOOL_URL_PREFIXES:
        if not prefix:
            continue
        if candidate == prefix or candidate.startswith(prefix + "/") or candidate.startswith(prefix + "?"):
            return tool_name
    return ""


def _normalize_tool_function_name(tool_name, method):
    tool = (tool_name or "tool").strip().lower().replace(" ", "-")
    verb = (method or "call").strip().lower()
    return f"{tool}__{verb}"


def _truncate_trace_result(result):
    if result is None:
        return ""
    if not isinstance(result, str):
        result = str(result)
    if len(result) > 4000:
        return result[:4000]
    return result


def _extract_request_body(data):
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    if isinstance(data, str):
        return data
    try:
        return json.dumps(data)
    except TypeError:
        return str(data)


def _extract_requests_body(kwargs):
    if "json" in kwargs and kwargs["json"] is not None:
        return _extract_request_body(kwargs["json"])
    if "data" in kwargs and kwargs["data"] is not None:
        return _extract_request_body(kwargs["data"])
    return ""


def _current_tool_trace_session():
    session = _TOOL_TRACE_SESSION.get()
    return session if isinstance(session, dict) else None


def _current_end_user_id():
    value = _END_USER_ID.get()
    return value if isinstance(value, str) else ""


def _build_tool_trace_headers(request_id="", run_id="", action_id="", trace_entry=None, tool_call_id="", tool_name="", function_name="", turn=None, end_user_id=""):
    session = _current_tool_trace_session()
    if not request_id and session:
        request_id = session.get("request_id", "")
    if not run_id and session:
        run_id = session.get("run_id", "")
    if not action_id and session:
        action_id = session.get("action_id", "")
    if not end_user_id:
        end_user_id = _current_end_user_id()

    if trace_entry is not None:
        tool_call_id = tool_call_id or trace_entry.get("tool_call_id", "")
        tool_name = tool_name or trace_entry.get("tool", "")
        function_name = function_name or trace_entry.get("function", "")
        if turn is None:
            turn = trace_entry.get("sequence")

    headers = {}
    if request_id:
        headers["X-Request-Id"] = str(request_id)
    if run_id:
        headers["X-Run-ID"] = str(run_id)
    if action_id:
        headers["X-Action-ID"] = str(action_id)
    if tool_call_id:
        headers["X-Tool-Call-Id"] = str(tool_call_id)
    if tool_name:
        headers["X-Tool-Name"] = str(tool_name)
    if function_name:
        headers["X-Tool-Function"] = str(function_name)
    if turn is not None:
        headers["X-Tool-Turn"] = str(turn)
    if end_user_id:
        headers["X-End-User-Id"] = str(end_user_id)
    return headers


def _merge_missing_headers(existing, additions):
    merged = dict(existing or {})
    existing_keys = {str(k).lower() for k in merged.keys()}
    for key, value in (additions or {}).items():
        if value in ("", None):
            continue
        if key.lower() in existing_keys:
            continue
        merged[key] = value
        existing_keys.add(key.lower())
    return merged


def _request_has_header(req, header_name):
    target = str(header_name).lower()
    for key, _ in req.header_items():
        if str(key).lower() == target:
            return True
    return False


def _add_missing_request_headers(req, headers):
    for key, value in (headers or {}).items():
        if value in ("", None):
            continue
        if _request_has_header(req, key):
            continue
        req.add_header(key, value)


def _begin_tool_trace_call(method, url, request_body="", tool_name=None, function_name=None, source="runtime"):
    session = _TOOL_TRACE_SESSION.get()
    if session is None:
        return None
    tool = (tool_name or _infer_tool_name_from_url(url)).strip()
    if not tool:
        return None
    session["sequence"] += 1
    call_id = f"user-call-{session['sequence']}-{uuid.uuid4().hex[:8]}"
    entry = {
        "tool_call_id": call_id,
        "tool": tool,
        "function": function_name or _normalize_tool_function_name(tool, method),
        "method": (method or "GET").upper(),
        "url": url,
        "request_body": request_body or "",
        "result": "",
        "status_code": 0,
        "source": source,
        "sequence": session["sequence"],
        "finalized": False,
    }
    session["tool_calls"].append(entry)
    return entry


def _finalize_tool_trace_call(entry, *, result=None, status_code=None):
    if entry is None or entry.get("finalized"):
        return
    if result is not None:
        entry["result"] = _truncate_trace_result(result)
    if status_code is not None:
        entry["status_code"] = int(status_code)
    entry["finalized"] = True


def _tool_calls_for_response(tool_calls):
    result = []
    for entry in tool_calls:
        result.append({
            "function": entry.get("function", ""),
            "tool": entry.get("tool", ""),
            "method": entry.get("method", ""),
            "url": entry.get("url", ""),
            "status_code": entry.get("status_code", 0),
            "source": entry.get("source", ""),
            "arguments": entry.get("request_body", ""),
            "result": entry.get("result", ""),
        })
    return result


def _decode_tool_result_payload(raw_result):
    if isinstance(raw_result, dict):
        return raw_result
    if not isinstance(raw_result, str):
        return {}
    try:
        payload = json.loads(raw_result)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    detail = payload.get("detail")
    if payload.get("code") or not isinstance(detail, str):
        return payload
    try:
        nested = json.loads(detail)
    except json.JSONDecodeError:
        return payload
    return nested if isinstance(nested, dict) else payload


def _promote_traced_tool_interrupts(result, tool_calls_made):
    if not isinstance(result, dict):
        return result
    if isinstance(result.get("approval_required"), dict) or isinstance(result.get("consent_required"), dict):
        return result

    for tool_call in tool_calls_made or []:
        payload = _decode_tool_result_payload(tool_call.get("result", ""))
        code = str(payload.get("code") or "").strip()
        tool_name = str(payload.get("tool") or tool_call.get("tool") or "").strip()
        if code == "CONSENT_REQUIRED":
            promoted = dict(result)
            promoted.update(_consent_required_result(payload, tool_name))
            return promoted
        if code == "APPROVAL_REQUIRED":
            promoted = dict(result)
            promoted.update(_approval_required_result(payload, tool_name))
            return promoted

    return result


def _flush_tool_trace_to_governance(run_id, tool_calls):
    if not run_id:
        return
    for turn, entry in enumerate(tool_calls):
        _post_tool_result(
            run_id=run_id,
            tool_call_id=entry.get("tool_call_id", ""),
            function_name=entry.get("function", ""),
            arguments=entry.get("request_body", ""),
            result=entry.get("result", ""),
            tool_id=entry.get("tool", ""),
            turn=turn,
        )


def _invoke_user_handler_with_trace(message, history, request_id="", run_id="", end_user_id="", resume=None):
    session = {
        "request_id": request_id,
        "run_id": run_id,
        "action_id": str((resume or {}).get("action_id", "")) if isinstance(resume, dict) else "",
        "tool_calls": [],
        "sequence": 0,
    }
    token = _TOOL_TRACE_SESSION.set(session)
    end_user_token = _END_USER_ID.set(end_user_id or _current_end_user_id())
    try:
        result = _call_user_handler_result(
            message,
            history,
            request_id=request_id,
            run_id=run_id,
            end_user_id=end_user_id,
            resume=resume,
        )
    except Exception:
        _flush_tool_trace_to_governance(run_id, session["tool_calls"])
        raise
    finally:
        _TOOL_TRACE_SESSION.reset(token)
        _END_USER_ID.reset(end_user_token)
    _flush_tool_trace_to_governance(run_id, session["tool_calls"])
    tool_calls_made = _tool_calls_for_response(session["tool_calls"])
    result = _promote_traced_tool_interrupts(result, tool_calls_made)
    return result, tool_calls_made


@contextlib.contextmanager
def _suppress_http_tool_trace():
    token = _SUPPRESS_HTTP_TOOL_TRACE.set(True)
    try:
        yield
    finally:
        _SUPPRESS_HTTP_TOOL_TRACE.reset(token)


class _TracedHTTPResponse:
    def __init__(self, response, trace_entry, status_code):
        self._response = response
        self._trace_entry = trace_entry
        self._status_code = status_code
        self._buffer = bytearray()

    def read(self, *args, **kwargs):
        data = self._response.read(*args, **kwargs)
        if data:
            self._buffer.extend(data)
        size = args[0] if args else -1
        if size in (-1, None) or data == b"":
            self._finalize()
        return data

    def __enter__(self):
        entered = self._response.__enter__()
        if entered is not self._response:
            self._response = entered
        return self

    def __exit__(self, exc_type, exc, tb):
        self._finalize()
        return self._response.__exit__(exc_type, exc, tb)

    def _finalize(self):
        if self._trace_entry is not None and not self._trace_entry.get("finalized"):
            payload = self._buffer.decode("utf-8", errors="replace")
            _finalize_tool_trace_call(self._trace_entry, result=payload, status_code=self._status_code)

    def close(self):
        self._finalize()
        return self._response.close()

    def __getattr__(self, name):
        return getattr(self._response, name)


def _install_url_rewrites():
    """Monkey-patch requests and urllib for URL rewrites and tool-call tracing.

    Reads TOOL_URL_REWRITES_JSON (set by the operator from deploy-time analysis).
    Maps detected placeholder base URLs in user code to real in-cluster tool URLs,
    so user code runs unmodified. The same HTTP hooks also capture user-handler
    tool calls that go through raw urllib/requests instead of Agent.call_tool().
    """
    global TOOL_URL_REWRITES, _HTTP_HOOKS_INSTALLED, _REQUESTS_ORIGINAL_SESSION_REQUEST
    TOOL_URL_REWRITES = _load_url_rewrites()

    if _HTTP_HOOKS_INSTALLED:
        return

    # Patch requests.Session.request if requests is available
    try:
        import requests as _requests
        _REQUESTS_ORIGINAL_SESSION_REQUEST = _requests.Session.request

        def _patched_request(self, method, url, **kwargs):
            rewritten_url = _rewrite_url(url)
            trace_entry = None
            if not _SUPPRESS_HTTP_TOOL_TRACE.get(False):
                trace_entry = _begin_tool_trace_call(
                    method=method,
                    url=rewritten_url,
                    request_body=_extract_requests_body(kwargs),
                    source="requests",
                )
            kwargs["headers"] = _merge_missing_headers(
                kwargs.get("headers"),
                _build_tool_trace_headers(trace_entry=trace_entry),
            )
            try:
                response = _REQUESTS_ORIGINAL_SESSION_REQUEST(self, method, rewritten_url, **kwargs)
            except Exception as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", 0)
                _finalize_tool_trace_call(trace_entry, result=str(exc), status_code=status_code)
                raise
            if trace_entry is not None:
                if kwargs.get("stream"):
                    _finalize_tool_trace_call(trace_entry, status_code=getattr(response, "status_code", 0))
                else:
                    _finalize_tool_trace_call(
                        trace_entry,
                        result=getattr(response, "text", ""),
                        status_code=getattr(response, "status_code", 0),
                    )
            return response

        _requests.Session.request = _patched_request
        _log("info", "http_tool_trace_installed", target="requests", rewrites=len(TOOL_URL_REWRITES))
    except ImportError:
        pass

    def _patched_urlopen(url, *args, **kwargs):
        method = "GET"
        request_body = ""
        target = url

        if isinstance(url, str):
            target = _rewrite_url(url)
            url = target
        elif isinstance(url, urllib.request.Request):
            target = _rewrite_url(url.full_url)
            url.full_url = target
            method = url.get_method()
            request_body = _extract_request_body(getattr(url, "data", None))
        else:
            target = str(url)

        trace_entry = None
        if not _SUPPRESS_HTTP_TOOL_TRACE.get(False):
            trace_entry = _begin_tool_trace_call(
                method=method,
                url=target,
                request_body=request_body,
                source="urllib",
            )
        if isinstance(url, urllib.request.Request):
            _add_missing_request_headers(url, _build_tool_trace_headers(trace_entry=trace_entry))
        try:
            response = _ORIGINAL_URLOPEN(url, *args, **kwargs)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            _finalize_tool_trace_call(trace_entry, result=error_body, status_code=exc.code)
            raise
        except Exception as exc:
            _finalize_tool_trace_call(trace_entry, result=str(exc), status_code=0)
            raise

        if trace_entry is None:
            return response
        return _TracedHTTPResponse(response, trace_entry, getattr(response, "status", 200))

    urllib.request.urlopen = _patched_urlopen
    _HTTP_HOOKS_INSTALLED = True
    _log("info", "http_tool_trace_installed", target="urllib", rewrites=len(TOOL_URL_REWRITES))


def _inject_platform_env():
    """Set SDK-compatible env vars so user code auto-routes through the platform.

    OpenAI, LangChain, and other SDKs read OPENAI_BASE_URL / OPENAI_API_KEY
    from the environment. By setting these before importing user code, all LLM
    calls transparently go through the LLM Gateway (and thus through Istio mesh).

    Does NOT overwrite env vars already set — user's explicit config wins.
    """
    gateway = os.environ.get("LLM_GATEWAY_URL", "")
    if not gateway:
        return

    # LLM_GATEWAY_URL is a base URL (e.g. .../v1/p/{name}).
    # Strip /chat/completions if present (safety net for legacy ConfigMaps).
    # The OpenAI SDK and _llm_completions_url() append it automatically.
    base_url = gateway
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]

    # Normalize so user code reads a clean base URL.
    os.environ["LLM_GATEWAY_URL"] = base_url

    # OpenAI SDK env vars
    if "OPENAI_BASE_URL" not in os.environ:
        os.environ["OPENAI_BASE_URL"] = base_url
    if "OPENAI_API_BASE" not in os.environ:
        os.environ["OPENAI_API_BASE"] = base_url
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "platform-managed"

    # Anthropic SDK env vars (same gateway, different SDK)
    if "ANTHROPIC_BASE_URL" not in os.environ:
        os.environ["ANTHROPIC_BASE_URL"] = base_url
    if "ANTHROPIC_API_KEY" not in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = "platform-managed"

    _log("info", "platform_env_injected", base_url=base_url)


class RunContext:
    """Context object passed to user handler functions (2-arg signature)."""

    def __init__(self):
        self.tools = {}  # {name: url} from TOOL_URLS
        self.llm_url = os.environ.get("LLM_GATEWAY_URL", LLM_GATEWAY_URL)
        self.model = LLM_MODEL
        self.system_prompt = SYSTEM_PROMPT
        self.session = {}  # conversation state (in-memory)

        # Build tool name → URL map
        for key, val in TOOL_URLS.items():
            name = key.replace("TOOL_URL_", "").lower().replace("_", "-")
            self.tools[name] = val


def _discover_user_handler():
    """Discover and return a callable from user code, or None for Tier 1 (built-in loop)."""
    global USER_HANDLER

    entry_point = os.environ.get("USER_ENTRY_POINT", "")
    if not entry_point:
        return

    # Convert filename to module name: "agent.py" → "agent", "src/main.py" → "src.main"
    module_name = entry_point
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    module_name = module_name.replace("/", ".").replace("\\", ".")

    # Ensure the mounted source tree and working directory are on the Python path.
    user_code_dir = os.environ.get("RUNAGENTS_USER_CODE_DIR", "").strip()
    if user_code_dir and user_code_dir not in sys.path:
        sys.path.insert(0, user_code_dir)

    # Ensure the working directory is on the Python path
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    if "." not in sys.path:
        sys.path.insert(0, ".")

    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        _log("warn", "failed to import user module", module=module_name, error=str(e))
        return

    # Priority 1: handler() function
    handler_func = getattr(mod, "handler", None)
    if callable(handler_func):
        USER_HANDLER = handler_func
        _log("info", "user_handler_discovered", type="handler_function", module=module_name)
        return

    # Priority 2: Known framework objects
    for attr_name in ("agent", "chain", "executor", "graph", "crew"):
        obj = getattr(mod, attr_name, None)
        if obj is not None:
            USER_HANDLER = _wrap_framework_object(obj, attr_name)
            if USER_HANDLER:
                _log("info", "user_handler_discovered", type=attr_name, module=module_name)
                return

    # Priority 3: main() function
    main_func = getattr(mod, "main", None)
    if callable(main_func):
        USER_HANDLER = main_func
        _log("info", "user_handler_discovered", type="main_function", module=module_name)
        return

    _log("warn", "no callable discovered in user module", module=module_name)


def _wrap_framework_object(obj, attr_name):
    """Wrap a known framework object (LangChain, LangGraph, CrewAI) into a callable."""
    obj_type = type(obj).__name__

    # LangChain AgentExecutor
    if obj_type == "AgentExecutor" or (hasattr(obj, "invoke") and hasattr(obj, "agent")):
        def langchain_handler(request, context=None):
            result = obj.invoke({"input": request["message"]})
            output = result.get("output", str(result))
            return {"response": output}
        return langchain_handler

    # LangGraph CompiledGraph
    if obj_type == "CompiledGraph" or (hasattr(obj, "invoke") and hasattr(obj, "nodes")):
        def langgraph_handler(request, context=None):
            try:
                from langchain_core.messages import HumanMessage
                msgs = [HumanMessage(content=request["message"])]
            except ImportError:
                msgs = [{"role": "user", "content": request["message"]}]
            result = obj.invoke({"messages": msgs})
            messages = result.get("messages", [])
            if messages:
                last = messages[-1]
                content = getattr(last, "content", str(last))
                return {"response": content}
            return {"response": str(result)}
        return langgraph_handler

    # Generic invocable (CrewAI Crew, or any object with .invoke/.run/.kickoff)
    for method_name in ("invoke", "run", "kickoff"):
        method = getattr(obj, method_name, None)
        if callable(method):
            def generic_handler(request, context=None, _m=method):
                result = _m(request["message"])
                if isinstance(result, dict):
                    return {"response": result.get("output", result.get("result", str(result)))}
                return {"response": str(result)}
            return generic_handler

    return None


def _normalize_user_handler_result(result):
    """Normalize a user handler return value into a response dict."""
    if isinstance(result, dict):
        normalized = dict(result)
        if "response" not in normalized:
            if "output" in normalized:
                normalized["response"] = normalized.get("output", "")
            else:
                normalized["response"] = json.dumps(result)
        return normalized
    return {"response": str(result)}


def _call_user_handler_result(message, history, request_id="", run_id="", end_user_id="", resume=None):
    """Call the user handler with the appropriate signature (sync or async)."""
    request = {
        "message": message,
        "history": history,
    }
    if request_id:
        request["request_id"] = request_id
    if run_id:
        request["run_id"] = run_id
    if end_user_id:
        request["user_id"] = end_user_id
    if resume is not None:
        request["resume"] = resume

    sig = inspect.signature(USER_HANDLER)

    # Count only positional-capable parameters.
    # VAR_KEYWORD (**kwargs) and KEYWORD_ONLY params must be excluded because
    # passing a positional arg to a **kwargs-only function raises:
    #   TypeError: main() takes 0 positional arguments but 1 was given
    positional = [
        p for p in sig.parameters.values()
        if p.kind not in (
            inspect.Parameter.VAR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    ]

    # Determine arguments based on positional parameter count
    if len(positional) >= 2:
        ctx = RunContext()
        ctx.session["history"] = history
        if request_id:
            ctx.session["request_id"] = request_id
        if run_id:
            ctx.session["run_id"] = run_id
        if end_user_id:
            ctx.session["user_id"] = end_user_id
        if resume is not None:
            ctx.session["resume"] = resume
            if isinstance(resume, dict) and resume.get("action_id"):
                ctx.session["action_id"] = str(resume.get("action_id"))
        args = (request, ctx)
    elif len(positional) == 1:
        param = positional[0]
        ann = param.annotation
        # Common names users give to a "message" parameter — pass just the string
        # so that def main(message): or def handler(text): work without users having
        # to know about the internal request dict shape.
        _str_param_names = {"message", "msg", "text", "query", "prompt", "input", "user_input"}
        if ann is str or (ann is inspect.Parameter.empty and param.name in _str_param_names):
            args = (request.get("message", ""),)
        else:
            args = (request,)
    else:
        # No positional parameters (includes def main(): and def main(**kwargs):)
        args = ()

    # Call handler - support both sync and async functions
    try:
        if inspect.iscoroutinefunction(USER_HANDLER):
            # Async handler - use asyncio.run to await it
            result = asyncio.run(USER_HANDLER(*args))
        else:
            # Sync handler - call directly
            result = USER_HANDLER(*args)
    except ApprovalRequired as e:
        return _approval_required_result(e.detail, e.tool_name)
    except ConsentRequired as e:
        return _consent_required_result(e.detail, e.tool_name)

    return _normalize_user_handler_result(result)


def _call_user_handler(message, history):
    """Backward-compatible wrapper returning only the response text."""
    return _call_user_handler_result(message, history).get("response", "")


# --- Structured Logging ---

def _log(level, msg, **kwargs):
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level,
        "agent": AGENT_NAME,
        "msg": msg,
    }
    entry.update(kwargs)
    print(json.dumps(entry), file=sys.stderr)


# --- Checkpoint Helpers ---

def _post_checkpoint(
    run_id,
    action_id,
    messages,
    pending_calls,
    resume_mode="",
    user_request=None,
    resume_state=None,
):
    """POST conversation checkpoint to governance for resume after approval.

    pending_calls is a list of PendingToolCall dicts — the blocked call first,
    then any subsequent calls from the same assistant message that haven't been
    attempted yet.
    """
    if not run_id or not action_id:
        _log("warn", "cannot checkpoint without run_id and action_id")
        return
    url = f"{GOVERNANCE_URL}/runs/{run_id}/checkpoint"
    payload = {
        "action_id": action_id,
        "messages": messages,
        "pending_calls": pending_calls,
        "tool_defs": TOOL_DEFINITIONS,
        "tool_routes": TOOL_ROUTES,
        "model": LLM_MODEL,
        "system_prompt": SYSTEM_PROMPT,
        "llm_gateway_url": LLM_GATEWAY_URL,
    }
    if resume_mode:
        payload["resume_mode"] = resume_mode
    if user_request is not None:
        payload["user_request"] = user_request
    if resume_state is not None:
        payload["resume_state"] = resume_state
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                headers={"Content-Type": "application/json"},
                                method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            _log("info", "checkpoint_stored", checkpoint_id=result.get("id", ""),
                 run_id=run_id, action_id=action_id)
    except Exception as e:
        _log("error", "checkpoint_failed", run_id=run_id, action_id=action_id, error=str(e))


def _user_handler_checkpoint_messages(message, history):
    messages = []
    for entry in history or []:
        if isinstance(entry, dict):
            role = entry.get("role", "user")
            content = entry.get("content", "")
            if role and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})
    return messages


def _checkpoint_user_handler_pause(run_id, action_id, message, history, request_id, end_user_id, resume_state, resume_kind=""):
    if not run_id or not action_id:
        _log("warn", "cannot checkpoint user handler pause without run_id and action_id")
        return
    state_payload = resume_state if isinstance(resume_state, dict) else {}
    if resume_kind:
        state_payload = dict(state_payload)
        state_payload["_runagents_resume_kind"] = resume_kind
    user_request = {
        "message": message,
        "history": history,
        "request_id": request_id,
        "run_id": run_id,
    }
    if end_user_id:
        user_request["user_id"] = end_user_id
    _post_checkpoint(
        run_id,
        action_id,
        _user_handler_checkpoint_messages(message, history),
        [],
        resume_mode="user_handler",
        user_request=user_request,
        resume_state=state_payload,
    )


def _build_user_handler_response(result, tool_calls_made, request_id, duration_ms):
    payload = dict(result)
    payload.setdefault("response", "")
    payload.setdefault("model", LLM_MODEL)
    payload.setdefault("usage", {})
    payload["tool_calls_made"] = tool_calls_made
    payload["duration_ms"] = duration_ms
    payload["request_id"] = request_id
    payload["handler"] = "user"
    return payload


def _get_checkpoint(run_id, action_id):
    """GET checkpoint from governance for resume."""
    url = f"{GOVERNANCE_URL}/runs/{run_id}/checkpoint/{action_id}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        _log("error", "checkpoint_fetch_failed", run_id=run_id, action_id=action_id, error=str(e))
        return None


def _post_tool_result(run_id, tool_call_id, function_name, arguments, result, tool_id, turn):
    """Report a completed tool execution to governance for platform-owned run history.
    Non-fatal — best-effort fire-and-forget."""
    if not run_id:
        return
    url = f"{GOVERNANCE_URL}/runs/{run_id}/tool-result"
    payload = {
        "tool_call_id": tool_call_id,
        "function_name": function_name,
        "arguments": arguments,
        "result": result,
        "tool_id": tool_id,
        "turn": turn,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as _:
            pass
    except Exception as e:
        _log("warn", "tool_result_report_failed", run_id=run_id,
             function=function_name, error=str(e))


def _collect_remaining_calls(tool_calls_slice, routes):
    """Build a list of PendingToolCall dicts from a slice of OpenAI tool_calls."""
    pending = []
    for tc in tool_calls_slice:
        name = tc["function"]["name"]
        args = tc["function"].get("arguments", "{}")
        route = routes.get(name, {}) if isinstance(routes, dict) else {}
        tool = route.get("tool", name.split("__")[0])
        method = route.get("method", "POST")
        path = route.get("path", "/")
        url_key = "TOOL_URL_" + tool.upper().replace("-", "_")
        base = TOOL_URLS.get(url_key, "")
        full_url = base.rstrip("/") + path
        pending.append({
            "tool_call_id": tc["id"],
            "function_name": name,
            "arguments": args,
            "method": method,
            "url": full_url,
            "tool_name": tool,
        })
    return pending


# --- LLM Calling ---

def _llm_completions_url():
    """Return the full chat completions URL, appending /chat/completions if needed."""
    url = os.environ.get("LLM_GATEWAY_URL", LLM_GATEWAY_URL)
    if not url.endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"
    return url


def call_llm(messages, tools=None, request_id=None):
    """POST to LLM Gateway and return the full response body."""
    payload = {"model": LLM_MODEL, "messages": messages}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if request_id:
        headers["X-Request-Id"] = request_id
    req = urllib.request.Request(
        _llm_completions_url(),
        data=data,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())
    return body


# --- Tool Execution ---

def _parse_tool_cache(tool_cache_list):
    """Parse a tool_cache list from the invoke body into a lookup dict.

    Input:  [{"function_name": "calc__add", "arguments": "{...}", "result": "..."}]
    Output: {("calc__add", "{...}"): "..."}
    """
    if not tool_cache_list:
        return None
    cache = {}
    for tc in tool_cache_list:
        key = (tc.get("function_name", ""), tc.get("arguments", ""))
        cache[key] = tc.get("result", "")
    return cache if cache else None


class ApprovalRequired(_ToolInterruptBase):
    """Raised when a tool call returns 403 APPROVAL_REQUIRED."""
    def __init__(self, tool_name, detail):
        self.tool_name = tool_name
        self.detail = detail
        super().__init__(f"Approval required for {tool_name}")


class ConsentRequired(_ToolInterruptBase):
    """Raised when a tool call returns 403 CONSENT_REQUIRED."""
    def __init__(self, tool_name, detail):
        self.tool_name = tool_name
        self.detail = detail
        super().__init__(f"Consent required for {tool_name}")


def _approval_required_result(detail, tool_name=""):
    normalized = dict(detail or {})
    normalized.setdefault("tool", normalized.get("tool") or tool_name)
    message = normalized.get("message") or (
        f"Tool '{normalized.get('tool') or tool_name or 'tool'}' requires approval before it can be used."
    )
    return {
        "response": message,
        "approval_required": normalized,
    }


def _resume_action_id(detail):
    if not isinstance(detail, dict):
        return ""
    for key in ("resume_id", "resumeId", "action_id", "actionId"):
        value = str(detail.get(key) or "").strip()
        if value:
            return value
    return ""


def _consent_required_result(detail, tool_name=""):
    normalized = dict(detail or {})
    normalized.setdefault("tool", normalized.get("tool") or tool_name)
    normalized.setdefault("code", "CONSENT_REQUIRED")
    message = normalized.get("message") or "You need to connect a tool before I can continue."
    auth_url = normalized.get("authorization_url", "") or normalized.get("authorizationUrl", "")
    resume_id = _resume_action_id(normalized)
    response = message
    if auth_url:
        response = f"{message} {auth_url}".strip()
    payload = {
        "code": "CONSENT_REQUIRED",
        "message": message,
        "response": response,
        "tool": normalized.get("tool", ""),
        "authorization_url": auth_url,
        "consent_required": normalized,
    }
    if resume_id:
        payload["resume_id"] = resume_id
    return payload


def _checkpoint_tool_loop_consent(run_id, detail, messages, pending_calls):
    action_id = _resume_action_id(detail)
    if not action_id:
        _log("warn", "cannot checkpoint consent without resume_id", run_id=run_id)
        return
    _post_checkpoint(run_id, action_id, messages, pending_calls)


def execute_tool_call(
    method,
    url,
    body=None,
    request_id=None,
    run_id=None,
    action_id=None,
    tool_call_id=None,
    tool_name=None,
    function_name=None,
    turn=None,
    source="sdk",
):
    """Execute an HTTP tool call and return the response body as string."""
    trace_entry = _begin_tool_trace_call(
        method=method,
        url=url,
        request_body=_extract_request_body(body),
        tool_name=tool_name,
        function_name=function_name,
        source=source,
    )
    headers = {"Content-Type": "application/json"}
    headers = _merge_missing_headers(
        headers,
        _build_tool_trace_headers(
            request_id=request_id,
            run_id=run_id,
            action_id=action_id,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            function_name=function_name,
            turn=turn,
            trace_entry=trace_entry,
        ),
    )
    data = body.encode() if body else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _suppress_http_tool_trace():
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
        _finalize_tool_trace_call(trace_entry, result=payload, status_code=getattr(resp, "status", 200))
        return payload
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        _finalize_tool_trace_call(trace_entry, result=error_body, status_code=e.code)
        if e.code == 403:
            # Check for APPROVAL_REQUIRED
            err_data = {}
            try:
                err_data = json.loads(error_body)
            except json.JSONDecodeError:
                # Non-JSON 403 bodies should not crash invoke; return as tool error.
                err_data = {}
            if err_data.get("code") == "APPROVAL_REQUIRED":
                raise ApprovalRequired(tool_name or function_name or url, err_data)
            if err_data.get("code") == "CONSENT_REQUIRED":
                raise ConsentRequired(tool_name or function_name or url, err_data)
        return json.dumps({"error": f"HTTP {e.code}", "detail": error_body})


def run_tool_loop(messages, tools, routes, request_id=None, run_id=None, tool_cache=None):
    """Run the LLM tool-calling loop until completion or max iterations.

    tool_cache: dict mapping (function_name, arguments_str) → cached result string.
    When provided, matching tool calls return the cached result instead of executing.
    """
    tool_calls_made = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    model_used = LLM_MODEL

    for iteration in range(MAX_TOOL_ITERATIONS):
        response = call_llm(messages, tools=tools if tools else None, request_id=request_id)
        model_used = response.get("model", LLM_MODEL)

        # Accumulate usage
        usage = response.get("usage", {})
        for key in total_usage:
            total_usage[key] += usage.get(key, 0)

        choice = response.get("choices", [{}])[0]
        finish_reason = choice.get("finish_reason", "stop")
        assistant_msg = choice.get("message", {})

        # Check for tool calls
        if assistant_msg.get("tool_calls"):
            # Append the assistant message (with tool_calls) to messages
            messages.append(assistant_msg)
            all_tool_calls = assistant_msg["tool_calls"]

            for tc_idx, tc in enumerate(all_tool_calls):
                func_name = tc["function"]["name"]
                arguments_str = tc["function"].get("arguments", "{}")
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}

                # Resolve route
                route = routes.get(func_name, {})
                tool_name = route.get("tool", func_name.split("__")[0])
                method = route.get("method", "POST")
                path = route.get("path", "/")

                # Resolve base URL
                url_key = "TOOL_URL_" + tool_name.upper().replace("-", "_")
                base_url = TOOL_URLS.get(url_key, "")

                # If arguments has a "path" override, use it
                if "path" in arguments and not route:
                    path = arguments.pop("path")

                full_url = base_url.rstrip("/") + path

                # Determine request body
                if method in ("POST", "PUT", "PATCH"):
                    body_str = arguments.get("body", json.dumps(arguments))
                else:
                    body_str = None

                _log("info", "tool_call", function=func_name, method=method,
                     url=full_url, iteration=iteration, request_id=request_id)

                # Check tool cache before executing (Tier 3 resume).
                cache_hit = False
                if tool_cache:
                    cache_key = (func_name, arguments_str)
                    if cache_key in tool_cache:
                        _log("info", "tool_cache_hit", function=func_name, request_id=request_id)
                        result = tool_cache[cache_key]
                        cache_hit = True

                if not cache_hit:
                    try:
                        result = execute_tool_call(
                            method,
                            full_url,
                            body=body_str,
                            request_id=request_id,
                            run_id=run_id,
                            tool_call_id=tc["id"],
                            tool_name=tool_name,
                            function_name=func_name,
                            turn=iteration,
                        )
                    except ApprovalRequired as e:
                        _log("info", "approval_required", function=func_name, request_id=request_id)
                        # Checkpoint conversation state for resume after approval.
                        # Collect the blocked call + all subsequent unexecuted calls
                        # so resume can execute ALL of them before calling LLM again.
                        detail = e.detail or {}
                        action_id = detail.get("action_id", "")
                        pending_calls = _collect_remaining_calls(all_tool_calls[tc_idx:], routes)
                        _post_checkpoint(run_id, action_id, messages, pending_calls)
                        # Return partial result with approval info
                        payload = _approval_required_result(detail, tool_name)
                        payload.update({
                            "model": model_used,
                            "usage": total_usage,
                            "tool_calls_made": tool_calls_made,
                        })
                        return payload
                    except ConsentRequired as e:
                        _log("info", "consent_required", function=func_name, request_id=request_id)
                        detail = e.detail or {}
                        pending_calls = _collect_remaining_calls(all_tool_calls[tc_idx:], routes)
                        _checkpoint_tool_loop_consent(run_id, detail, messages, pending_calls)
                        payload = _consent_required_result(detail, tool_name)
                        payload.update({
                            "model": model_used,
                            "usage": total_usage,
                            "tool_calls_made": tool_calls_made,
                        })
                        return payload

                tool_calls_made.append({
                    "function": func_name,
                    "method": method,
                    "url": full_url,
                })

                _log("info", "tool_result", function=func_name,
                     result_length=len(result) if result else 0, request_id=request_id)

                # Report to governance for platform-owned run history.
                # This enables the platform to reconstruct full context on resume
                # without relying solely on the checkpoint.
                _post_tool_result(
                    run_id=run_id,
                    tool_call_id=tc["id"],
                    function_name=func_name,
                    arguments=arguments_str,
                    result=result or "",
                    tool_id=tool_name,
                    turn=iteration,
                )

                # Append tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result or "",
                })

            continue  # Loop back to call LLM with tool results

        # No tool calls — return the text response
        content = assistant_msg.get("content", "")
        return {
            "response": content,
            "model": model_used,
            "usage": total_usage,
            "tool_calls_made": tool_calls_made,
        }

    # Exceeded max iterations
    _log("warn", "max_tool_iterations_reached", iterations=MAX_TOOL_ITERATIONS, request_id=request_id)
    return {
        "response": "I reached the maximum number of tool call iterations. Here's what I have so far.",
        "model": model_used,
        "usage": total_usage,
        "tool_calls_made": tool_calls_made,
    }


# --- HTTP Handler ---

class AgentHandler(BaseHTTPRequestHandler):
    """Handles GET / (health), GET /readyz (readiness), POST /invoke (chat),
    and POST /invoke/stream (SSE streaming chat)."""

    def do_GET(self):
        if self.path == "/" or self.path == "/healthz":
            tools_count = len(TOOL_DEFINITIONS)
            has_user_code = USER_HANDLER is not None
            self._json(200, {"status": "ok", "agent": AGENT_NAME, "model": LLM_MODEL,
                             "tools": tools_count, "user_code": has_user_code})
        elif self.path == "/readyz":
            self._handle_readyz()
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/invoke":
            self._handle_invoke()
        elif self.path == "/invoke/stream":
            self._handle_invoke_stream()
        elif self.path.startswith("/resume/"):
            action_id = self.path[len("/resume/"):]
            stream = action_id.endswith("/stream")
            if stream:
                action_id = action_id[:-len("/stream")]
            self._handle_resume(action_id, stream=stream)
        else:
            self._json(404, {"error": "not found"})

    def _handle_readyz(self):
        """Check LLM Gateway reachability."""
        health_url = LLM_GATEWAY_URL.rsplit("/v1/", 1)[0] + "/healthz"
        try:
            req = urllib.request.Request(health_url, method="GET")
            with urllib.request.urlopen(req, timeout=5):
                pass
            self._json(200, {"status": "ready", "llm_gateway": "reachable"})
        except Exception as e:
            self._json(503, {"status": "not ready", "llm_gateway": str(e)})

    def _handle_invoke(self):
        request_id = self.headers.get("X-Request-Id", str(uuid.uuid4()))
        run_id = self.headers.get("X-Run-ID", "")
        end_user_id = self.headers.get("X-End-User-Id", "")
        start_time = time.time()
        end_user_token = _END_USER_ID.set(end_user_id)

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except (json.JSONDecodeError, ValueError):
            self._json(400, {"error": "invalid JSON body"})
            _END_USER_ID.reset(end_user_token)
            return

        message = body.get("message", "")
        history = body.get("history", [])
        if not run_id:
            run_id = body.get("run_id", "")

        # Parse tool_cache from body (Tier 3 resume: re-invocation with cached results).
        tool_cache = _parse_tool_cache(body.get("tool_cache"))

        if not message:
            self._json(400, {"error": "message is required"})
            _END_USER_ID.reset(end_user_token)
            return

        try:
            # Tier 2: User handler takes priority
            if USER_HANDLER is not None:
                _log("info", "invoking_user_handler", request_id=request_id)
                result, tool_calls_made = _invoke_user_handler_with_trace(
                    message,
                    history,
                    request_id=request_id,
                    run_id=run_id,
                    end_user_id=end_user_id,
                )
                duration_ms = int((time.time() - start_time) * 1000)
                approval_detail = result.get("approval_required") if isinstance(result, dict) else None
                consent_detail = result.get("consent_required") if isinstance(result, dict) else None
                if isinstance(approval_detail, dict):
                    action_id = approval_detail.get("action_id", "")
                    _checkpoint_user_handler_pause(
                        run_id,
                        action_id,
                        message,
                        history,
                        request_id,
                        end_user_id,
                        result.get("resume"),
                    )
                if isinstance(consent_detail, dict):
                    action_id = _resume_action_id(consent_detail)
                    if action_id:
                        _checkpoint_user_handler_pause(
                            run_id,
                            action_id,
                            message,
                            history,
                            request_id,
                            end_user_id,
                            result.get("resume"),
                            resume_kind="consent",
                        )
                result = _build_user_handler_response(result, tool_calls_made, request_id, duration_ms)
                _log("info", "invoke_complete", duration_ms=duration_ms,
                     tool_calls=len(tool_calls_made), handler="user", request_id=request_id)
                self._json(200, result)
                return

            # Tier 1: Built-in tool loop
            # Build messages: system prompt + conversation history + current user message
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for entry in history:
                role = entry.get("role", "user")
                content = entry.get("content", "")
                if role and content:
                    messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": message})

            if TOOL_DEFINITIONS:
                result = run_tool_loop(messages, TOOL_DEFINITIONS, TOOL_ROUTES,
                                       request_id=request_id, run_id=run_id,
                                       tool_cache=tool_cache)
            else:
                # No tools — simple single-shot call
                resp = call_llm(messages, request_id=request_id)
                choice = resp.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                result = {
                    "response": content,
                    "model": resp.get("model", LLM_MODEL),
                    "usage": resp.get("usage", {}),
                    "tool_calls_made": [],
                }

            duration_ms = int((time.time() - start_time) * 1000)
            result["duration_ms"] = duration_ms
            result["request_id"] = request_id
            _log("info", "invoke_complete", duration_ms=duration_ms,
                 tool_calls=len(result.get("tool_calls_made", [])), request_id=request_id)
            self._json(200, result)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            _log("error", "llm_gateway_error", status=e.code, detail=error_body, request_id=request_id)
            self._json(502, {"error": f"LLM Gateway returned {e.code}", "detail": error_body, "request_id": request_id})
        except urllib.error.URLError as e:
            _log("error", "llm_gateway_unreachable", reason=str(e.reason), request_id=request_id)
            self._json(502, {"error": f"LLM Gateway unreachable: {e.reason}", "request_id": request_id})
        except Exception as e:
            _log("error", "unexpected_error", error=str(e), request_id=request_id)
            self._json(500, {"error": str(e), "request_id": request_id})
        finally:
            _END_USER_ID.reset(end_user_token)

    def _handle_invoke_stream(self):
        """SSE streaming endpoint for tool-calling conversations."""
        request_id = self.headers.get("X-Request-Id", str(uuid.uuid4()))
        run_id = self.headers.get("X-Run-ID", "")
        end_user_id = self.headers.get("X-End-User-Id", "")
        end_user_token = _END_USER_ID.set(end_user_id)

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except (json.JSONDecodeError, ValueError):
            self._json(400, {"error": "invalid JSON body"})
            _END_USER_ID.reset(end_user_token)
            return

        message = body.get("message", "")
        history = body.get("history", [])
        if not run_id:
            run_id = body.get("run_id", "")

        # Parse tool_cache from body (Tier 3 resume).
        tool_cache = _parse_tool_cache(body.get("tool_cache"))

        if not message:
            self._json(400, {"error": "message is required"})
            _END_USER_ID.reset(end_user_token)
            return

        # Set SSE headers
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Request-Id", request_id)
        self.end_headers()

        try:
            # Tier 2: User handler takes priority
            if USER_HANDLER is not None:
                _log("info", "streaming_user_handler", request_id=request_id)
                result, tool_calls_made = _invoke_user_handler_with_trace(
                    message,
                    history,
                    request_id=request_id,
                    run_id=run_id,
                    end_user_id=end_user_id,
                )
                approval_detail = result.get("approval_required") if isinstance(result, dict) else None
                consent_detail = result.get("consent_required") if isinstance(result, dict) else None
                if isinstance(approval_detail, dict):
                    action_id = approval_detail.get("action_id", "")
                    _checkpoint_user_handler_pause(
                        run_id,
                        action_id,
                        message,
                        history,
                        request_id,
                        end_user_id,
                        result.get("resume"),
                    )
                if isinstance(consent_detail, dict):
                    action_id = _resume_action_id(consent_detail)
                    if action_id:
                        _checkpoint_user_handler_pause(
                            run_id,
                            action_id,
                            message,
                            history,
                            request_id,
                            end_user_id,
                            result.get("resume"),
                            resume_kind="consent",
                        )
                for tool_call in tool_calls_made:
                    self._write_sse({
                        "type": "tool_call",
                        "tool": tool_call.get("function") or tool_call.get("tool", ""),
                        "arguments": tool_call.get("arguments", ""),
                    })
                    self._write_sse({
                        "type": "tool_result",
                        "tool": tool_call.get("function") or tool_call.get("tool", ""),
                        "result": (tool_call.get("result", "") or "")[:1000],
                    })
                response_text = result.get("response", "")
                if response_text:
                    self._write_sse({"type": "content", "delta": response_text})
                if isinstance(approval_detail, dict):
                    self._write_sse({
                        "type": "approval_required",
                        "tool": approval_detail.get("tool", ""),
                        "detail": approval_detail,
                    })
                if isinstance(consent_detail, dict):
                    self._write_sse({
                        "type": "consent_required",
                        "tool": consent_detail.get("tool", ""),
                        "detail": consent_detail,
                    })
                self._write_sse_done(LLM_MODEL, tool_calls_made)
                return

            # Tier 1: Built-in tool loop with SSE events
            # Build messages
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for entry in history:
                role = entry.get("role", "user")
                content = entry.get("content", "")
                if role and content:
                    messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": message})

            tool_calls_made = []
            tools = TOOL_DEFINITIONS if TOOL_DEFINITIONS else None

            for iteration in range(MAX_TOOL_ITERATIONS):
                response = call_llm(messages, tools=tools, request_id=request_id)
                choice = response.get("choices", [{}])[0]
                assistant_msg = choice.get("message", {})

                if assistant_msg.get("tool_calls"):
                    messages.append(assistant_msg)
                    all_tcs = assistant_msg["tool_calls"]

                    for tc_idx, tc in enumerate(all_tcs):
                        func_name = tc["function"]["name"]
                        arguments_str = tc["function"].get("arguments", "{}")

                        # Send tool_call event
                        self._write_sse({"type": "tool_call", "tool": func_name, "arguments": arguments_str})

                        try:
                            arguments = json.loads(arguments_str)
                        except json.JSONDecodeError:
                            arguments = {}

                        route = TOOL_ROUTES.get(func_name, {})
                        tool_name = route.get("tool", func_name.split("__")[0])
                        method = route.get("method", "POST")
                        path = route.get("path", "/")
                        url_key = "TOOL_URL_" + tool_name.upper().replace("-", "_")
                        base_url = TOOL_URLS.get(url_key, "")
                        full_url = base_url.rstrip("/") + path

                        body_str = arguments.get("body", json.dumps(arguments)) if method in ("POST", "PUT", "PATCH") else None

                        # Check tool cache before executing (Tier 3 resume).
                        cache_hit = False
                        if tool_cache:
                            cache_key = (func_name, arguments_str)
                            if cache_key in tool_cache:
                                _log("info", "tool_cache_hit", function=func_name, request_id=request_id)
                                result = tool_cache[cache_key]
                                cache_hit = True

                        if not cache_hit:
                            try:
                                result = execute_tool_call(
                                    method,
                                    full_url,
                                    body=body_str,
                                    request_id=request_id,
                                    run_id=run_id,
                                    tool_call_id=tc["id"],
                                    tool_name=tool_name,
                                    function_name=func_name,
                                    turn=iteration,
                                )
                            except ApprovalRequired as e:
                                detail = e.detail or {}
                                action_id = detail.get("action_id", "")
                                pending_calls = _collect_remaining_calls(all_tcs[tc_idx:], TOOL_ROUTES)
                                _post_checkpoint(run_id, action_id, messages, pending_calls)
                                self._write_sse({"type": "approval_required", "tool": func_name, "detail": detail})
                                self._write_sse_done(response.get("model", LLM_MODEL), tool_calls_made)
                                return
                            except ConsentRequired as e:
                                detail = e.detail or {}
                                pending_calls = _collect_remaining_calls(all_tcs[tc_idx:], TOOL_ROUTES)
                                _checkpoint_tool_loop_consent(run_id, detail, messages, pending_calls)
                                self._write_sse({"type": "consent_required", "tool": tool_name, "detail": detail})
                                self._write_sse({"type": "content", "delta": _consent_required_result(detail, tool_name).get("response", "")})
                                self._write_sse_done(response.get("model", LLM_MODEL), tool_calls_made)
                                return

                        tool_calls_made.append({"function": func_name, "method": method, "url": full_url})

                        # Send tool_result event
                        self._write_sse({"type": "tool_result", "tool": func_name, "result": result[:1000] if result else ""})

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result or "",
                        })

                    continue  # Loop back

                # Final text response — send as content event
                content = assistant_msg.get("content", "")
                self._write_sse({"type": "content", "delta": content})
                self._write_sse_done(response.get("model", LLM_MODEL), tool_calls_made)
                return

            # Max iterations
            self._write_sse({"type": "content", "delta": "Maximum tool iterations reached."})
            self._write_sse_done(LLM_MODEL, tool_calls_made)

        except Exception as e:
            _log("error", "stream_error", error=str(e), request_id=request_id)
            self._write_sse({"type": "error", "message": str(e)})
            self.wfile.write(b"data: [DONE]\n\n")
        finally:
            _END_USER_ID.reset(end_user_token)
            self.wfile.flush()

    def _handle_resume(self, action_id, stream=False):
        """Resume a paused conversation after approval by restoring checkpoint.

        Executes ALL pending tool calls (the blocked one + any subsequent calls
        from the same assistant message), then continues the tool loop.
        """
        request_id = self.headers.get("X-Request-Id", str(uuid.uuid4()))
        run_id = self.headers.get("X-Run-ID", "")
        end_user_id = self.headers.get("X-End-User-Id", "")

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except (json.JSONDecodeError, ValueError):
            body = {}

        if not end_user_id:
            end_user_id = body.get("user_id", "")
        end_user_token = _END_USER_ID.set(end_user_id)

        try:
            if not run_id:
                run_id = body.get("run_id", "")

            if not run_id:
                self._json(400, {"error": "X-Run-ID header or run_id in body is required"})
                return

            _log("info", "resume_start", action_id=action_id, run_id=run_id, request_id=request_id)

            tools = TOOL_DEFINITIONS
            routes = TOOL_ROUTES

            # Tier 1 resume: fetch checkpoint from governance to restore conversation.
            # (Tier 3 re-invocation goes through /invoke with tool_cache instead.)
            checkpoint = _get_checkpoint(run_id, action_id)
            if not checkpoint:
                self._json(404, {"error": f"checkpoint for action {action_id} not found"})
                return

            if checkpoint.get("resume_mode") == "user_handler":
                if stream:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.send_header("X-Request-Id", request_id)
                    self.end_headers()
                self._resume_user_handler_from_checkpoint(checkpoint, action_id, request_id, run_id, end_user_id, stream=stream)
                return

            messages = checkpoint.get("messages", [])
            pending_calls = checkpoint.get("pending_calls", [])
            tools = checkpoint.get("tool_defs", TOOL_DEFINITIONS)
            routes = checkpoint.get("tool_routes", TOOL_ROUTES)

            if pending_calls is None:
                pending_calls = []
            if not messages:
                self._json(400, {"error": "no conversation context for resume"})
                return

            # Set up SSE headers early if streaming
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.send_header("X-Request-Id", request_id)
                self.end_headers()

            # Execute ALL pending tool calls from the checkpoint
            tool_calls_made = []
            for pc_idx, pc in enumerate(pending_calls):
                method = pc.get("method", "POST")
                url = pc.get("url", "")
                func_name = pc.get("function_name", "")
                tool_call_id = pc.get("tool_call_id", "")
                arguments_str = pc.get("arguments", "{}")

                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}

                body_str = arguments.get("body", json.dumps(arguments)) if method in ("POST", "PUT", "PATCH") else None

                _log("info", "resume_retry_tool", function=func_name, method=method, url=url,
                     index=pc_idx, total=len(pending_calls), request_id=request_id)

                if stream:
                    self._write_sse({"type": "tool_call", "tool": func_name, "arguments": arguments_str})

                try:
                    result = execute_tool_call(
                        method,
                        url,
                        body=body_str,
                        request_id=request_id,
                        run_id=run_id,
                        action_id=action_id,
                        tool_call_id=tool_call_id,
                        tool_name=pc.get("tool_name", ""),
                        function_name=func_name,
                        turn=pc_idx,
                    )
                except ApprovalRequired as e:
                    detail = e.detail or {}
                    new_action_id = detail.get("action_id", "")
                    remaining = pending_calls[pc_idx:]
                    _post_checkpoint(run_id, new_action_id, messages, remaining)
                    if stream:
                        self._write_sse({"type": "approval_required", "tool": func_name, "detail": detail})
                        self._write_sse_done(LLM_MODEL, tool_calls_made)
                    else:
                        self._json(200, {
                            "response": f"Tool '{func_name}' requires another approval.",
                            "model": LLM_MODEL,
                            "approval_required": detail,
                            "tool_calls_made": tool_calls_made,
                            "request_id": request_id,
                        })
                    return
                except ConsentRequired as e:
                    detail = e.detail or {}
                    remaining = pending_calls[pc_idx:]
                    _checkpoint_tool_loop_consent(run_id, detail, messages, remaining)
                    payload = _consent_required_result(detail, pc.get("tool_name", "") or func_name)
                    if stream:
                        self._write_sse({"type": "consent_required", "tool": pc.get("tool_name", "") or func_name, "detail": detail})
                        self._write_sse({"type": "content", "delta": payload.get("response", "")})
                        self._write_sse_done(LLM_MODEL, tool_calls_made)
                    else:
                        payload.update({
                            "model": LLM_MODEL,
                            "tool_calls_made": tool_calls_made,
                            "request_id": request_id,
                        })
                        self._json(200, payload)
                    return
                except Exception as e:
                    _log("error", "resume_tool_call_failed", function=func_name, error=str(e), request_id=request_id)
                    if stream:
                        self._write_sse({"type": "error", "message": f"Tool call failed: {e}"})
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    else:
                        self._json(502, {"error": f"Tool call failed on resume: {e}", "request_id": request_id})
                    return

                tool_calls_made.append({"function": func_name, "method": method, "url": url})

                if stream:
                    self._write_sse({"type": "tool_result", "tool": func_name, "result": (result or "")[:1000]})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result or "",
                })

            # All pending calls executed — continue the tool loop
            if stream:
                for iteration in range(MAX_TOOL_ITERATIONS):
                    response = call_llm(messages, tools=tools if tools else None, request_id=request_id)
                    choice = response.get("choices", [{}])[0]
                    assistant_msg = choice.get("message", {})

                    if assistant_msg.get("tool_calls"):
                        messages.append(assistant_msg)
                        all_tcs = assistant_msg["tool_calls"]
                        for tc_idx, tc in enumerate(all_tcs):
                            fn = tc["function"]["name"]
                            args_str = tc["function"].get("arguments", "{}")
                            self._write_sse({"type": "tool_call", "tool": fn, "arguments": args_str})

                            try:
                                args = json.loads(args_str)
                            except json.JSONDecodeError:
                                args = {}

                            route = routes.get(fn, {}) if isinstance(routes, dict) else {}
                            tn = route.get("tool", fn.split("__")[0])
                            m = route.get("method", "POST")
                            p = route.get("path", "/")
                            uk = "TOOL_URL_" + tn.upper().replace("-", "_")
                            bu = TOOL_URLS.get(uk, "")
                            fu = bu.rstrip("/") + p
                            bs = args.get("body", json.dumps(args)) if m in ("POST", "PUT", "PATCH") else None

                            try:
                                res = execute_tool_call(
                                    m,
                                    fu,
                                    body=bs,
                                    request_id=request_id,
                                    run_id=run_id,
                                    tool_call_id=tc["id"],
                                    tool_name=tn,
                                    function_name=fn,
                                    turn=iteration,
                                )
                            except ApprovalRequired as ae:
                                det = ae.detail or {}
                                aid = det.get("action_id", "")
                                remaining_calls = _collect_remaining_calls(all_tcs[tc_idx:], routes)
                                _post_checkpoint(run_id, aid, messages, remaining_calls)
                                self._write_sse({"type": "approval_required", "tool": fn, "detail": det})
                                self._write_sse_done(response.get("model", LLM_MODEL), tool_calls_made)
                                return
                            except ConsentRequired as ce:
                                det = ce.detail or {}
                                remaining_calls = _collect_remaining_calls(all_tcs[tc_idx:], routes)
                                _checkpoint_tool_loop_consent(run_id, det, messages, remaining_calls)
                                self._write_sse({"type": "consent_required", "tool": tn, "detail": det})
                                self._write_sse({"type": "content", "delta": _consent_required_result(det, tn).get("response", "")})
                                self._write_sse_done(response.get("model", LLM_MODEL), tool_calls_made)
                                return

                            tool_calls_made.append({"function": fn, "method": m, "url": fu})
                            self._write_sse({"type": "tool_result", "tool": fn, "result": (res or "")[:1000]})
                            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": res or ""})
                        continue

                    content = assistant_msg.get("content", "")
                    self._write_sse({"type": "content", "delta": content})
                    self._write_sse_done(response.get("model", LLM_MODEL), tool_calls_made)
                    return

                self._write_sse({"type": "content", "delta": "Maximum tool iterations reached."})
                self._write_sse_done(LLM_MODEL, tool_calls_made)
            else:
                # Non-streaming resume — continue with run_tool_loop
                loop_result = run_tool_loop(messages, tools, routes, request_id=request_id, run_id=run_id)
                # Merge tool calls
                all_calls = tool_calls_made + loop_result.get("tool_calls_made", [])
                loop_result["tool_calls_made"] = all_calls
                loop_result["request_id"] = request_id
                _log("info", "resume_complete", action_id=action_id, run_id=run_id, request_id=request_id)
                self._json(200, loop_result)
        finally:
            _END_USER_ID.reset(end_user_token)

    def _write_sse(self, data):
        """Write a single SSE event."""
        line = f"data: {json.dumps(data)}\n\n"
        self.wfile.write(line.encode())
        self.wfile.flush()

    def _write_sse_done(self, model, tool_calls_made):
        """Write the done event and [DONE] sentinel."""
        self._write_sse({"type": "done", "model": model, "tool_calls_made": tool_calls_made})
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _resume_user_handler_from_checkpoint(self, checkpoint, action_id, request_id, run_id, end_user_id, stream=False):
        user_request = checkpoint.get("user_request") or {}
        if not isinstance(user_request, dict):
            user_request = {}
        resume_state = checkpoint.get("resume_state") or {}
        resume_kind = ""
        if isinstance(resume_state, dict):
            resume_kind = str(resume_state.get("_runagents_resume_kind", "")).strip()
            if "_runagents_resume_kind" in resume_state:
                resume_state = dict(resume_state)
                resume_state.pop("_runagents_resume_kind", None)
        message = user_request.get("message", "")
        history = user_request.get("history", [])
        resumed_user_id = end_user_id or user_request.get("user_id", "")

        resume_payload = {
            "action_id": action_id,
            "state": resume_state,
        }
        if resume_kind == "consent":
            resume_payload["consented"] = True
        else:
            resume_payload["approved"] = True

        result, tool_calls_made = _invoke_user_handler_with_trace(
            message,
            history,
            request_id=request_id,
            run_id=run_id,
            end_user_id=resumed_user_id,
            resume=resume_payload,
        )
        approval_detail = result.get("approval_required") if isinstance(result, dict) else None
        consent_detail = result.get("consent_required") if isinstance(result, dict) else None
        if isinstance(approval_detail, dict):
            new_action_id = approval_detail.get("action_id", "")
            _checkpoint_user_handler_pause(
                run_id,
                new_action_id,
                message,
                history,
                request_id,
                resumed_user_id,
                result.get("resume"),
            )
        if isinstance(consent_detail, dict):
            new_action_id = _resume_action_id(consent_detail)
            if new_action_id:
                _checkpoint_user_handler_pause(
                    run_id,
                    new_action_id,
                    message,
                    history,
                    request_id,
                    resumed_user_id,
                    result.get("resume"),
                    resume_kind="consent",
                )

        if stream:
            for tool_call in tool_calls_made:
                self._write_sse({
                    "type": "tool_call",
                    "tool": tool_call.get("function") or tool_call.get("tool", ""),
                    "arguments": tool_call.get("arguments", ""),
                })
                self._write_sse({
                    "type": "tool_result",
                    "tool": tool_call.get("function") or tool_call.get("tool", ""),
                    "result": (tool_call.get("result", "") or "")[:1000],
                })
            if result.get("response"):
                self._write_sse({"type": "content", "delta": result.get("response", "")})
            if isinstance(approval_detail, dict):
                self._write_sse({
                    "type": "approval_required",
                    "tool": approval_detail.get("tool", ""),
                    "detail": approval_detail,
                })
            if isinstance(consent_detail, dict):
                self._write_sse({
                    "type": "consent_required",
                    "tool": consent_detail.get("tool", ""),
                    "detail": consent_detail,
                })
            self._write_sse_done(result.get("model", LLM_MODEL), tool_calls_made)
            return

        payload = _build_user_handler_response(result, tool_calls_made, request_id, 0)
        self._json(200, payload)

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # Suppress default access logs — we use structured logging instead
        pass


def main():
    _inject_platform_env()
    _init_tools()
    _install_url_rewrites()
    _discover_user_handler()
    _log("info", "runtime_starting", port=PORT, model=LLM_MODEL,
         llm_gateway=LLM_GATEWAY_URL, tools=len(TOOL_DEFINITIONS),
         user_handler=USER_HANDLER is not None)
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    server = ThreadedHTTPServer(("0.0.0.0", PORT), AgentHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _log("info", "shutting_down")
        server.shutdown()


if __name__ == "__main__":
    main()
