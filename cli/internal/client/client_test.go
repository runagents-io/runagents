package client

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

type roundTripperFunc func(*http.Request) (*http.Response, error)

func (f roundTripperFunc) RoundTrip(req *http.Request) (*http.Response, error) {
	return f(req)
}

func TestNormalizeEndpointAddsTargetAPIPrefix(t *testing.T) {
	got := normalizeEndpoint("https://1406e38143ac0e57.try.runagents.io/")
	want := "https://1406e38143ac0e57.try.runagents.io/api/v1"
	if got != want {
		t.Fatalf("expected %q, got %q", want, got)
	}
}

func TestNormalizeEndpointPromotesWorkspacePath(t *testing.T) {
	got := normalizeEndpoint("https://acme.runagents.io/workspaces/revops")
	want := "https://acme.runagents.io/api/v1/workspaces/revops"
	if got != want {
		t.Fatalf("expected %q, got %q", want, got)
	}
}

func TestNormalizePathPreservesCleanResourcePath(t *testing.T) {
	got := normalizePath("/agents/billing-agent")
	want := "/agents/billing-agent"
	if got != want {
		t.Fatalf("expected %q, got %q", want, got)
	}
}

func TestClientUsesBearerOnlyAndTargetPath(t *testing.T) {
	var capturedPath string
	var workspaceHeader string
	var apiKeyHeader string
	var authHeader string
	c := NewClient("https://acme.runagents.io/workspaces/revops", "ra_ws_test")
	c.httpClient = &http.Client{
		Transport: roundTripperFunc(func(r *http.Request) (*http.Response, error) {
			capturedPath = r.URL.Path
			workspaceHeader = r.Header.Get("X-Workspace-Namespace")
			apiKeyHeader = r.Header.Get("X-RunAgents-API-Key")
			authHeader = r.Header.Get("Authorization")
			return &http.Response{
				StatusCode: http.StatusOK,
				Body:       io.NopCloser(strings.NewReader(`[]`)),
				Header:     make(http.Header),
			}, nil
		}),
	}
	if _, err := c.Get("/tools"); err != nil {
		t.Fatalf("get tools: %v", err)
	}

	if capturedPath != "/api/v1/workspaces/revops/tools" {
		t.Fatalf("expected target API path, got %q", capturedPath)
	}
	if workspaceHeader != "" {
		t.Fatalf("expected no workspace header, got %q", workspaceHeader)
	}
	if apiKeyHeader != "" {
		t.Fatalf("expected no API key header, got %q", apiKeyHeader)
	}
	if authHeader != "Bearer ra_ws_test" {
		t.Fatalf("expected bearer auth, got %q", authHeader)
	}
}

func TestClientGetWithQuery(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if got := r.URL.Path; got != "/api/v1/runs" {
			t.Fatalf("expected path /api/v1/runs, got %s", got)
		}
		if got := r.URL.Query().Get("agent_id"); got != "calendar-agent" {
			t.Fatalf("expected agent_id query, got %q", got)
		}
		if got := r.Header.Get("X-Workspace-Namespace"); got != "" {
			t.Fatalf("expected no workspace namespace header, got %q", got)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	}))
	defer server.Close()

	c := NewClient(server.URL, "")
	query := url.Values{}
	query.Set("agent_id", "calendar-agent")

	body, err := c.GetWithQuery("/runs", query)
	if err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}

	var payload map[string]string
	if err := json.Unmarshal(body, &payload); err != nil {
		t.Fatalf("expected JSON response, got error: %v", err)
	}
	if payload["status"] != "ok" {
		t.Fatalf("expected status ok, got %q", payload["status"])
	}
}

func TestClientBuildURLMergesExistingQuery(t *testing.T) {
	c := NewClient("https://api.runagents.io/base", "")
	query := url.Values{}
	query.Set("status", "PAUSED_APPROVAL")

	target, err := c.buildURL("/runs?agent_id=calendar-agent", query)
	if err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}

	parsed, err := url.Parse(target)
	if err != nil {
		t.Fatalf("expected parsable URL, got error: %v", err)
	}
	if parsed.Query().Get("agent_id") != "calendar-agent" {
		t.Fatalf("expected agent_id to be preserved, got %q", parsed.Query().Get("agent_id"))
	}
	if parsed.Query().Get("status") != "PAUSED_APPROVAL" {
		t.Fatalf("expected status to be merged, got %q", parsed.Query().Get("status"))
	}
}

func TestClientDeleteUsesSharedRequestFlow(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodDelete {
			t.Fatalf("expected DELETE method, got %s", r.Method)
		}
		w.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	c := NewClient(server.URL, "")
	if err := c.Delete("/agents/demo"); err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}
}

func TestClientPutBuildsJSONRequest(t *testing.T) {
	c := NewClient("https://api.runagents.io", "token")
	req, err := c.newRequest(http.MethodPut, "/policies/demo", nil, map[string]any{"name": "demo"})
	if err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}
	if req.Method != http.MethodPut {
		t.Fatalf("expected PUT method, got %s", req.Method)
	}
	if req.Header.Get("Content-Type") != "application/json" {
		t.Fatalf("expected json content type, got %q", req.Header.Get("Content-Type"))
	}
	buf := new(bytes.Buffer)
	if _, err := buf.ReadFrom(req.Body); err != nil {
		t.Fatalf("read body: %v", err)
	}
	if got := buf.String(); got != `{"name":"demo"}` {
		t.Fatalf("unexpected body: %s", got)
	}
}
