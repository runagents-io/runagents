package commands

import (
	"fmt"
	"testing"
)

func TestEstimateItemCount(t *testing.T) {
	if got := estimateItemCount([]interface{}{1, 2, 3}); got != 3 {
		t.Fatalf("expected 3, got %d", got)
	}
	if got := estimateItemCount(map[string]interface{}{"a": 1, "b": 2}); got != 2 {
		t.Fatalf("expected 2, got %d", got)
	}
	if got := estimateItemCount("unknown"); got != 0 {
		t.Fatalf("expected 0, got %d", got)
	}
}

func TestDecodeJSONBody(t *testing.T) {
	value, err := decodeJSONBody([]byte(`{"items":[1,2]}`))
	if err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}
	parsed, ok := value.(map[string]interface{})
	if !ok {
		t.Fatalf("expected object map, got %T", value)
	}
	if _, ok := parsed["items"]; !ok {
		t.Fatalf("expected items key in parsed response")
	}
}

func TestDecodeJSONBodyInvalid(t *testing.T) {
	if _, err := decodeJSONBody([]byte(`{`)); err == nil {
		t.Fatalf("expected decode error for invalid JSON")
	}
}

func TestContextExportErrorCount(t *testing.T) {
	payload := map[string]interface{}{
		"errors": map[string]interface{}{
			"agents": "failed",
			"tools":  "failed",
		},
	}
	if got := contextExportErrorCount(payload); got != 2 {
		t.Fatalf("expected 2 errors, got %d", got)
	}
	if got := contextExportErrorCount(map[string]interface{}{}); got != 0 {
		t.Fatalf("expected 0 errors, got %d", got)
	}
}

func TestEnrichContextExportPayloadAddsMissingGovernanceResources(t *testing.T) {
	payload := map[string]any{
		"generated_at": "2026-04-09T00:00:00Z",
		"endpoint":     "https://api.runagents.io",
		"namespace":    "default",
		"resources": map[string]any{
			"agents": []any{map[string]any{"name": "billing-agent"}},
		},
	}

	responses := map[string]any{
		"/api/tools":                        []any{map[string]any{"name": "stripe-api"}},
		"/api/model-providers":              []any{map[string]any{"name": "openai"}},
		"/api/policies":                     []any{map[string]any{"name": "billing-write-approval"}},
		"/api/identity-providers":           []any{map[string]any{"name": "google-oidc"}},
		"/api/settings/approval-connectors": []any{map[string]any{"id": "ac_123"}},
		"/governance/requests":              []any{},
		"/api/deploy-drafts":                []any{},
	}

	err := enrichContextExportPayload(func(path string) (any, error) {
		value, ok := responses[path]
		if !ok {
			return nil, fmt.Errorf("unexpected path: %s", path)
		}
		return value, nil
	}, payload, false, "https://api.runagents.io", "default")
	if err != nil {
		t.Fatalf("enrichContextExportPayload: %v", err)
	}

	resources := ensureContextExportObject(payload, "resources")
	for _, key := range []string{"agents", "tools", "model_providers", "policies", "identity_providers", "approval_connectors", "approvals", "deploy_drafts"} {
		if _, ok := resources[key]; !ok {
			t.Fatalf("expected resource %q to be present", key)
		}
	}
	meta := ensureContextExportObject(payload, "meta")
	if meta["policies_count"] != 1 {
		t.Fatalf("expected policies_count=1, got %#v", meta["policies_count"])
	}
}

func TestEnrichContextExportPayloadStrictModeFailsOnFetchError(t *testing.T) {
	payload := newContextExportPayload("https://api.runagents.io", "default")
	err := enrichContextExportPayload(func(path string) (any, error) {
		if path == "/api/policies" {
			return nil, fmt.Errorf("policies unavailable")
		}
		return []any{}, nil
	}, payload, true, "https://api.runagents.io", "default")
	if err == nil {
		t.Fatalf("expected strict mode fetch error")
	}
}
