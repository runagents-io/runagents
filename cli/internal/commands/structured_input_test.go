package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDecodeStructuredDataJSON(t *testing.T) {
	var payload map[string]any
	if err := decodeStructuredData([]byte(`{"name":"policy-a","enabled":true}`), ".json", &payload); err != nil {
		t.Fatalf("expected JSON decode to succeed, got error: %v", err)
	}
	if payload["name"] != "policy-a" {
		t.Fatalf("expected name policy-a, got %v", payload["name"])
	}
}

func TestDecodeStructuredDataYAML(t *testing.T) {
	var payload map[string]any
	if err := decodeStructuredData([]byte("name: connector-a\nenabled: true\n"), ".yaml", &payload); err != nil {
		t.Fatalf("expected YAML decode to succeed, got error: %v", err)
	}
	if payload["name"] != "connector-a" {
		t.Fatalf("expected name connector-a, got %v", payload["name"])
	}
}

func TestDecodeStructuredFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "policy.yaml")
	if err := os.WriteFile(path, []byte("name: workspace-write\n"), 0o600); err != nil {
		t.Fatalf("write temp file: %v", err)
	}

	var payload map[string]any
	if err := decodeStructuredFile(path, &payload); err != nil {
		t.Fatalf("expected decode to succeed, got error: %v", err)
	}
	if payload["name"] != "workspace-write" {
		t.Fatalf("expected name workspace-write, got %v", payload["name"])
	}
}

func TestDecodeStructuredDataInvalid(t *testing.T) {
	var payload map[string]any
	if err := decodeStructuredData([]byte("{"), ".json", &payload); err == nil {
		t.Fatalf("expected invalid structured document to fail")
	}
}
