package client

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"
)

func TestClientGetWithQuery(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if got := r.URL.Path; got != "/runs" {
			t.Fatalf("expected path /runs, got %s", got)
		}
		if got := r.URL.Query().Get("agent_id"); got != "calendar-agent" {
			t.Fatalf("expected agent_id query, got %q", got)
		}
		if got := r.Header.Get("X-Workspace-Namespace"); got != "trial-123" {
			t.Fatalf("expected workspace namespace header, got %q", got)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	}))
	defer server.Close()

	c := NewClient(server.URL, "", "trial-123")
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
	c := NewClient("https://api.runagents.io/base", "", "default")
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

	c := NewClient(server.URL, "", "default")
	if err := c.Delete("/api/agents/demo"); err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}
}
