"""
Tests for runagents_runtime._call_user_handler parameter detection.

These tests were added after discovering that def main(**kwargs) caused:
  TypeError: main() takes 0 positional arguments but 1 was given
because the old code counted VAR_KEYWORD params as positional.
"""
import io
import json
import sys
import inspect
import unittest
import urllib.error
import urllib.request
from unittest import mock
from pathlib import Path

# Patch environment so the runtime module loads without needing K8s / LLM
import os
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("TOOL_DEFINITIONS_JSON", "[]")
os.environ.setdefault("TOOL_ROUTES_JSON", "{}")
os.environ.setdefault("LLM_GATEWAY_URL", "http://localhost:8080/v1/chat/completions")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")

import runagents_runtime as rt


def _set_handler(fn):
    rt.USER_HANDLER = fn


class TestCallUserHandlerSignatures(unittest.TestCase):
    """
    Verify _call_user_handler correctly infers positional argument count for
    all realistic user-defined handler signatures.
    """

    def setUp(self):
        rt.USER_HANDLER = None

    # --- 0-arg handlers ---

    def test_no_params(self):
        """def main(): — canonical 0-arg handler."""
        called_with = []
        def main():
            called_with.append(())
            return "ok"
        _set_handler(main)
        result = rt._call_user_handler("hello", [])
        self.assertEqual(called_with, [()])
        self.assertEqual(result, "ok")

    def test_kwargs_only(self):
        """def main(**kwargs): — must be called with 0 positional args."""
        called_with = []
        def main(**kwargs):
            called_with.append(kwargs)
            return "ok"
        _set_handler(main)
        # Before fix this raised: TypeError: main() takes 0 positional arguments but 1 was given
        result = rt._call_user_handler("hello", [])
        self.assertEqual(called_with, [{}])
        self.assertEqual(result, "ok")

    # --- 1-arg handlers ---

    def test_one_positional_param(self):
        """def main(request): — receives {"message": ..., "history": [...]}."""
        received = []
        def main(request):
            received.append(request)
            return "ok"
        _set_handler(main)
        rt._call_user_handler("hello", ["prev"])
        self.assertEqual(received[0]["message"], "hello")
        self.assertEqual(received[0]["history"], ["prev"])

    def test_varargs(self):
        """def main(*args): — receives (request,) as first element."""
        received = []
        def main(*args):
            received.append(args)
            return "ok"
        _set_handler(main)
        rt._call_user_handler("hello", [])
        self.assertEqual(len(received[0]), 1)
        self.assertEqual(received[0][0]["message"], "hello")

    def test_one_positional_plus_kwargs(self):
        """def main(request, **kwargs): — 1 positional + **kwargs."""
        received = []
        def main(request, **kwargs):
            received.append(request)
            return "ok"
        _set_handler(main)
        rt._call_user_handler("hello", [])
        self.assertEqual(received[0]["message"], "hello")

    # --- 2-arg handlers ---

    def test_two_positional_params(self):
        """def main(request, ctx): — receives request + RunContext."""
        received = []
        def main(request, ctx):
            received.append((request, ctx))
            return "ok"
        _set_handler(main)
        rt._call_user_handler("hello", [])
        req, ctx = received[0]
        self.assertEqual(req["message"], "hello")
        self.assertIsInstance(ctx, rt.RunContext)

    def test_two_positional_plus_kwargs(self):
        """def main(request, ctx, **kwargs): — 2 positional + **kwargs."""
        received = []
        def main(request, ctx, **kwargs):
            received.append((request, ctx))
            return "ok"
        _set_handler(main)
        rt._call_user_handler("hello", [])
        req, ctx = received[0]
        self.assertEqual(req["message"], "hello")

    # --- Return value normalisation ---

    def test_returns_dict_response_key(self):
        def main():
            return {"response": "from dict"}
        _set_handler(main)
        result = rt._call_user_handler("hi", [])
        self.assertEqual(result, "from dict")

    def test_returns_dict_output_key(self):
        def main():
            return {"output": "from output"}
        _set_handler(main)
        result = rt._call_user_handler("hi", [])
        self.assertEqual(result, "from output")

    def test_returns_string(self):
        def main():
            return "plain string"
        _set_handler(main)
        result = rt._call_user_handler("hi", [])
        self.assertEqual(result, "plain string")

    def test_returns_non_string_coerced(self):
        def main():
            return 42
        _set_handler(main)
        result = rt._call_user_handler("hi", [])
        self.assertEqual(result, "42")

    def test_call_user_handler_result_passes_resume_metadata(self):
        received = {}

        def main(request, ctx):
            received["request"] = request
            received["session"] = dict(ctx.session)
            return {"response": "ok"}

        _set_handler(main)
        result = rt._call_user_handler_result(
            "hello",
            [{"role": "user", "content": "prev"}],
            request_id="req-1",
            run_id="run-1",
            end_user_id="alice@example.com",
            resume={"approved": True, "action_id": "act-1", "state": {"draft": "follow-up"}},
        )

        self.assertEqual(result["response"], "ok")
        self.assertEqual(received["request"]["request_id"], "req-1")
        self.assertEqual(received["request"]["run_id"], "run-1")
        self.assertEqual(received["request"]["user_id"], "alice@example.com")
        self.assertTrue(received["request"]["resume"]["approved"])
        self.assertEqual(received["request"]["resume"]["action_id"], "act-1")
        self.assertEqual(received["session"]["request_id"], "req-1")
        self.assertEqual(received["session"]["run_id"], "run-1")
        self.assertEqual(received["session"]["user_id"], "alice@example.com")
        self.assertEqual(received["session"]["resume"]["state"]["draft"], "follow-up")


class TestParameterKindClassification(unittest.TestCase):
    """
    Directly verify that the positional param filter matches expected counts
    for every Python parameter kind.
    """

    def _positional_count(self, fn):
        sig = inspect.signature(fn)
        positional = [
            p for p in sig.parameters.values()
            if p.kind not in (
                inspect.Parameter.VAR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ]
        return len(positional)

    def test_no_params(self):             self.assertEqual(self._positional_count(lambda: None), 0)
    def test_one_positional(self):        self.assertEqual(self._positional_count(lambda x: None), 1)
    def test_two_positional(self):        self.assertEqual(self._positional_count(lambda x, y: None), 2)
    def test_varargs(self):               self.assertEqual(self._positional_count(lambda *a: None), 1)
    def test_kwargs_only(self):           self.assertEqual(self._positional_count(lambda **kw: None), 0)
    def test_positional_plus_kwargs(self): self.assertEqual(self._positional_count(lambda x, **kw: None), 1)
    def test_keyword_only(self):
        # def f(*, key): — keyword-only, should not count
        def f(*, key): pass
        self.assertEqual(self._positional_count(f), 0)


class TestExecuteToolCallHTTP403(unittest.TestCase):
    def _http_error(self, body: bytes, code: int = 403):
        return urllib.error.HTTPError(
            url="http://tool.example.com/execute",
            code=code,
            msg="error",
            hdrs=None,
            fp=io.BytesIO(body),
        )

    def test_non_json_403_returns_tool_error_payload(self):
        with mock.patch("runagents_runtime.urllib.request.urlopen", side_effect=self._http_error(b"forbidden")):
            result = rt.execute_tool_call("POST", "http://tool.example.com/execute", body='{"x":1}')
        payload = json.loads(result)
        self.assertEqual(payload.get("error"), "HTTP 403")
        self.assertEqual(payload.get("detail"), "forbidden")

    def test_consent_required_403_raises(self):
        body = b'{"code":"CONSENT_REQUIRED","authorization_url":"https://example.com/oauth"}'
        with mock.patch("runagents_runtime.urllib.request.urlopen", side_effect=self._http_error(body)):
            with self.assertRaises(rt.ConsentRequired):
                rt.execute_tool_call("POST", "http://tool.example.com/execute", body='{"x":1}')

    def test_approval_required_403_raises(self):
        body = b'{"code":"APPROVAL_REQUIRED","action_id":"act-1"}'
        with mock.patch("runagents_runtime.urllib.request.urlopen", side_effect=self._http_error(body)):
            with self.assertRaises(rt.ApprovalRequired):
                rt.execute_tool_call("POST", "http://tool.example.com/execute", body='{"x":1}')


class _FakeHTTPResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self, *args, **kwargs):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def close(self):
        return None


class TestConsentInterrupts(unittest.TestCase):
    def setUp(self):
        rt.USER_HANDLER = None

    def test_run_tool_loop_returns_structured_consent_required_payload(self):
        routes = {
            "email__list_messages": {
                "tool": "email",
                "method": "GET",
                "path": "/gmail/v1/users/me/messages",
            }
        }
        llm_response = {
            "model": "test-model",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "choices": [{
                "finish_reason": "tool_calls",
                "message": {
                    "tool_calls": [{
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "email__list_messages",
                            "arguments": "{\"maxResults\":3}",
                        },
                    }],
                },
            }],
        }

        with mock.patch.dict(rt.TOOL_URLS, {"TOOL_URL_EMAIL": "http://tool.example.com/email"}, clear=False), \
                mock.patch("runagents_runtime.call_llm", return_value=llm_response), \
                mock.patch(
                    "runagents_runtime.execute_tool_call",
                    side_effect=rt.ConsentRequired("email", {
                        "code": "CONSENT_REQUIRED",
                        "message": "Connect Gmail to continue.",
                        "authorization_url": "https://example.com/oauth",
                    }),
                ):
            result = rt.run_tool_loop(
                [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "show my mail"}],
                [],
                routes,
                request_id="req-1",
                run_id="run-1",
            )

        self.assertEqual(result["code"], "CONSENT_REQUIRED")
        self.assertEqual(result["message"], "Connect Gmail to continue.")
        self.assertEqual(result["authorization_url"], "https://example.com/oauth")
        self.assertEqual(result["response"], "Connect Gmail to continue. https://example.com/oauth")
        self.assertEqual(result["consent_required"]["tool"], "email")
        self.assertEqual(result["model"], "test-model")

    def test_user_handler_tool_consent_returns_structured_payload(self):
        with mock.patch.dict(os.environ, {
            "TOOL_URL_EMAIL": "http://tool.example.com/email",
        }, clear=False):
            rt._init_tools()
            rt._install_url_rewrites()

            def handler():
                from runagents import Agent
                return Agent().call_tool(
                    "email",
                    path="/gmail/v1/users/me/messages",
                    method="GET",
                )

            _set_handler(handler)

            with mock.patch(
                "runagents_runtime.execute_tool_call",
                side_effect=rt.ConsentRequired("email", {
                    "code": "CONSENT_REQUIRED",
                    "message": "Connect Gmail to continue.",
                    "authorization_url": "https://example.com/oauth",
                }),
            ):
                result = rt._call_user_handler_result(
                    "show my mail",
                    [],
                    request_id="req-1",
                    run_id="run-1",
                    end_user_id="alice@example.com",
                )

        self.assertEqual(result["code"], "CONSENT_REQUIRED")
        self.assertEqual(result["message"], "Connect Gmail to continue.")
        self.assertEqual(result["authorization_url"], "https://example.com/oauth")
        self.assertEqual(result["tool"], "email")
        self.assertEqual(result["consent_required"]["tool"], "email")

    def test_promotes_consent_required_from_traced_tool_result(self):
        result = {"response": "I hit a Gmail permissions issue."}
        tool_calls = [{
            "function": "email__get",
            "tool": "email",
            "method": "GET",
            "url": "http://tool.example.com/email/gmail/v1/users/me/messages?maxResults=3",
            "status_code": 403,
            "source": "urllib",
            "arguments": "",
            "result": json.dumps({
                "code": "CONSENT_REQUIRED",
                "message": "User must grant OAuth consent",
                "authorization_url": "https://example.com/oauth",
                "resume_id": "resume-1",
            }),
        }]

        promoted = rt._promote_traced_tool_interrupts(result, tool_calls)

        self.assertEqual(promoted["code"], "CONSENT_REQUIRED")
        self.assertEqual(promoted["authorization_url"], "https://example.com/oauth")
        self.assertEqual(promoted["resume_id"], "resume-1")
        self.assertEqual(promoted["tool"], "email")
        self.assertEqual(promoted["response"], "User must grant OAuth consent https://example.com/oauth")

    def test_promotes_nested_consent_required_from_http_error_detail(self):
        result = {"response": "I hit a Gmail permissions issue."}
        tool_calls = [{
            "function": "email__get",
            "tool": "email",
            "method": "GET",
            "url": "http://tool.example.com/email/gmail/v1/users/me/messages?maxResults=3",
            "status_code": 403,
            "source": "urllib",
            "arguments": "",
            "result": json.dumps({
                "error": "HTTP 403",
                "detail": json.dumps({
                    "code": "CONSENT_REQUIRED",
                    "message": "User must grant OAuth consent",
                    "authorization_url": "https://example.com/oauth",
                }),
            }),
        }]

        promoted = rt._promote_traced_tool_interrupts(result, tool_calls)

        self.assertEqual(promoted["code"], "CONSENT_REQUIRED")
        self.assertEqual(promoted["authorization_url"], "https://example.com/oauth")
        self.assertEqual(promoted["tool"], "email")

    def test_langgraph_toolnode_bubbles_consent_required_to_runtime(self):
        try:
            from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
            from langchain_core.tools import tool
            from langgraph.graph import START, StateGraph
            from langgraph.graph.message import add_messages
            from langgraph.prebuilt import ToolNode
            from typing import Annotated, TypedDict
        except Exception as exc:  # pragma: no cover - optional dependency path
            self.skipTest(f"langgraph unavailable: {exc}")

        with mock.patch.dict(os.environ, {
            "TOOL_URL_EMAIL": "http://tool.example.com/email",
        }, clear=False):
            rt._init_tools()
            rt._install_url_rewrites()

            def handler():
                @tool
                def needs_consent() -> str:
                    """Test tool."""
                    from runagents import Agent
                    return Agent().call_tool(
                        "email",
                        path="/gmail/v1/users/me/messages",
                        method="GET",
                    )

                class GraphState(TypedDict):
                    messages: Annotated[list[AnyMessage], add_messages]

                def graph_agent(state: GraphState):
                    return {
                        "messages": [
                            AIMessage(
                                content="",
                                tool_calls=[{
                                    "name": "needs_consent",
                                    "args": {},
                                    "id": "call-1",
                                    "type": "tool_call",
                                }],
                            )
                        ]
                    }

                builder = StateGraph(GraphState)
                builder.add_node("agent", graph_agent)
                builder.add_node("tools", ToolNode([needs_consent]))
                builder.add_edge(START, "agent")
                builder.add_edge("agent", "tools")
                graph = builder.compile()
                graph.invoke({"messages": [HumanMessage(content="show my mail")]})
                return {"response": "unexpected"}

            _set_handler(handler)

            with mock.patch(
                "runagents_runtime.execute_tool_call",
                side_effect=rt.ConsentRequired("email", {
                    "code": "CONSENT_REQUIRED",
                    "message": "Connect Gmail to continue.",
                    "authorization_url": "https://example.com/oauth",
                }),
            ):
                result = rt._call_user_handler_result(
                    "show my mail",
                    [],
                    request_id="req-1",
                    run_id="run-1",
                    end_user_id="alice@example.com",
                )

        self.assertEqual(result["code"], "CONSENT_REQUIRED")
        self.assertEqual(result["message"], "Connect Gmail to continue.")
        self.assertEqual(result["authorization_url"], "https://example.com/oauth")
        self.assertEqual(result["tool"], "email")


class TestUserHandlerToolTracing(unittest.TestCase):
    def setUp(self):
        rt.USER_HANDLER = None
        rt.TOOL_URL_REWRITES = {}
        rt._TOOL_TRACE_SESSION.set(None)
        rt._SUPPRESS_HTTP_TOOL_TRACE.set(False)

    def test_agent_sdk_tool_calls_are_traced_and_forwarded(self):
        with mock.patch.dict(os.environ, {
            "TOOL_URL_CALENDAR": "http://tool.example.com/calendar",
        }, clear=False):
            rt._init_tools()
            rt._install_url_rewrites()

            def handler():
                from runagents import Agent
                payload = Agent().call_tool("calendar", payload={"query": "today"})
                return payload["summary"]

            _set_handler(handler)
            posted = []

            with mock.patch("runagents_runtime._ORIGINAL_URLOPEN", return_value=_FakeHTTPResponse(b'{"summary":"brief"}')) as mocked_urlopen, \
                    mock.patch("runagents_runtime._post_tool_result", side_effect=lambda **kwargs: posted.append(kwargs)):
                response, tool_calls = rt._invoke_user_handler_with_trace("hello", [], "req-1", "run-1", "alice@example.com")

            self.assertEqual(response["response"], "brief")
            self.assertEqual(len(tool_calls), 1)
            self.assertEqual(tool_calls[0]["tool"], "calendar")
            self.assertEqual(tool_calls[0]["function"], "calendar")
            self.assertEqual(tool_calls[0]["method"], "POST")
            self.assertEqual(tool_calls[0]["status_code"], 200)
            self.assertEqual(tool_calls[0]["source"], "agent_sdk")
            self.assertIn('"query": "today"', tool_calls[0]["arguments"])
            self.assertEqual(len(posted), 1)
            self.assertEqual(posted[0]["tool_id"], "calendar")
            self.assertEqual(posted[0]["function_name"], "calendar")
            self.assertEqual(posted[0]["run_id"], "run-1")
            sent_request = mocked_urlopen.call_args.args[0]
            sent_headers = {k.lower(): v for k, v in sent_request.header_items()}
            self.assertEqual(sent_headers["x-run-id"], "run-1")
            self.assertEqual(sent_headers["x-request-id"], "req-1")
            self.assertEqual(sent_headers["x-end-user-id"], "alice@example.com")
            self.assertEqual(sent_headers["x-tool-name"], "calendar")
            self.assertEqual(sent_headers["x-tool-function"], "calendar")
            self.assertIn("x-tool-call-id", sent_headers)

    def test_raw_urllib_tool_calls_are_traced(self):
        with mock.patch.dict(os.environ, {
            "TOOL_URL_KNOWLEDGE_BASE": "http://tool.example.com/knowledge-base",
        }, clear=False):
            rt._init_tools()
            rt._install_url_rewrites()

            def handler():
                req = urllib.request.Request(
                    "http://tool.example.com/knowledge-base/search",
                    data=b'{"query":"risks"}',
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                return body["answer"]

            _set_handler(handler)
            posted = []

            with mock.patch("runagents_runtime._ORIGINAL_URLOPEN", return_value=_FakeHTTPResponse(b'{"answer":"focus on rollout"}')) as mocked_urlopen, \
                    mock.patch("runagents_runtime._post_tool_result", side_effect=lambda **kwargs: posted.append(kwargs)):
                response, tool_calls = rt._invoke_user_handler_with_trace("hello", [], "req-2", "run-2", "bob@example.com")

            self.assertEqual(response["response"], "focus on rollout")
            self.assertEqual(len(tool_calls), 1)
            self.assertEqual(tool_calls[0]["tool"], "knowledge-base")
            self.assertEqual(tool_calls[0]["function"], "knowledge-base__post")
            self.assertEqual(tool_calls[0]["method"], "POST")
            self.assertEqual(tool_calls[0]["source"], "urllib")
            self.assertIn('"query":"risks"', tool_calls[0]["arguments"])
            self.assertEqual(len(posted), 1)
            self.assertEqual(posted[0]["tool_id"], "knowledge-base")
            self.assertEqual(posted[0]["function_name"], "knowledge-base__post")
            self.assertEqual(posted[0]["result"], '{"answer":"focus on rollout"}')
            sent_request = mocked_urlopen.call_args.args[0]
            sent_headers = {k.lower(): v for k, v in sent_request.header_items()}
            self.assertEqual(sent_headers["x-run-id"], "run-2")
            self.assertEqual(sent_headers["x-request-id"], "req-2")
            self.assertEqual(sent_headers["x-end-user-id"], "bob@example.com")
            self.assertEqual(sent_headers["x-tool-name"], "knowledge-base")
            self.assertEqual(sent_headers["x-tool-function"], "knowledge-base__post")
            self.assertEqual(sent_headers["x-tool-turn"], "1")

    def test_resumed_tool_calls_forward_action_id(self):
        with mock.patch.dict(os.environ, {
            "TOOL_URL_CALENDAR": "http://tool.example.com/calendar",
        }, clear=False):
            rt._init_tools()
            rt._install_url_rewrites()

            def handler():
                from runagents import Agent
                payload = Agent().call_tool("calendar", payload={"query": "tomorrow"})
                return payload["summary"]

            _set_handler(handler)

            with mock.patch("runagents_runtime._ORIGINAL_URLOPEN", return_value=_FakeHTTPResponse(b'{"summary":"scheduled"}')) as mocked_urlopen:
                response, tool_calls = rt._invoke_user_handler_with_trace(
                    "hello",
                    [],
                    "req-3",
                    "run-3",
                    "alice@example.com",
                    resume={"approved": True, "action_id": "act-1"},
                )

            self.assertEqual(response["response"], "scheduled")
            self.assertEqual(len(tool_calls), 1)
            sent_request = None
            for call in mocked_urlopen.call_args_list:
                candidate = call.args[0]
                if getattr(candidate, "full_url", "").startswith("http://tool.example.com/calendar"):
                    sent_request = candidate
                    break
            self.assertIsNotNone(sent_request)
            sent_headers = {k.lower(): v for k, v in sent_request.header_items()}
            self.assertEqual(sent_headers["x-action-id"], "act-1")


class TestStrictOutboundMode(unittest.TestCase):
    def setUp(self):
        rt.TOOL_URL_REWRITES = {}
        rt.OUTBOUND_MODE = "direct"

    def test_strict_mode_blocks_unbound_external_url(self):
        with mock.patch.dict(os.environ, {"RUNAGENTS_OUTBOUND_MODE": "strict"}, clear=False):
            rt._init_tools()
            with self.assertRaises(rt.UnboundOutboundURL):
                rt._rewrite_url("https://api.stripe.com/v1/charges")

    def test_strict_mode_allows_internal_cluster_url(self):
        with mock.patch.dict(os.environ, {"RUNAGENTS_OUTBOUND_MODE": "strict"}, clear=False):
            rt._init_tools()
            url = "http://calendar.default.svc.cluster.local/events"
            self.assertEqual(rt._rewrite_url(url), url)

    def test_strict_mode_allows_rewritten_bound_url(self):
        with mock.patch.dict(os.environ, {
            "RUNAGENTS_OUTBOUND_MODE": "strict",
            "TOOL_URL_REWRITES_JSON": json.dumps({
                "https://api.stripe.com": "http://istio-egressgateway.istio-system.svc.cluster.local/runagents-tools/default/stripe"
            }),
        }, clear=False):
            rt._init_tools()
            rt.TOOL_URL_REWRITES = rt._load_url_rewrites()
            rewritten = rt._rewrite_url("https://api.stripe.com/v1/charges")
            self.assertEqual(
                rewritten,
                "http://istio-egressgateway.istio-system.svc.cluster.local/runagents-tools/default/stripe/v1/charges",
            )


if __name__ == "__main__":
    unittest.main()
