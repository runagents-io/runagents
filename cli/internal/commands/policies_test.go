package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadPolicyApplyRequestEnvelope(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "policy.yaml")
	if err := os.WriteFile(path, []byte(`
name: workspace-write
spec:
  policies:
    - permission: approval_required
      operations: [POST]
      resource: https://www.googleapis.com/*
`), 0o600); err != nil {
		t.Fatalf("write policy file: %v", err)
	}

	req, err := loadPolicyApplyRequest(path, "")
	if err != nil {
		t.Fatalf("loadPolicyApplyRequest: %v", err)
	}
	if req.Name != "workspace-write" {
		t.Fatalf("expected policy name workspace-write, got %q", req.Name)
	}
	if len(req.Spec.Policies) != 1 || req.Spec.Policies[0].Permission != "approval_required" {
		t.Fatalf("unexpected policy spec: %#v", req.Spec.Policies)
	}
}

func TestLoadPolicyApplyRequestRawSpecWithOverride(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "policy.json")
	if err := os.WriteFile(path, []byte(`{"policies":[{"permission":"allow","operations":["GET"],"resource":"https://api.stripe.com/*"}]}`), 0o600); err != nil {
		t.Fatalf("write policy file: %v", err)
	}

	req, err := loadPolicyApplyRequest(path, "stripe-read")
	if err != nil {
		t.Fatalf("loadPolicyApplyRequest: %v", err)
	}
	if req.Name != "stripe-read" {
		t.Fatalf("expected override name, got %q", req.Name)
	}
	if len(req.Spec.Policies) != 1 || req.Spec.Policies[0].Resource != "https://api.stripe.com/*" {
		t.Fatalf("unexpected policy rules: %#v", req.Spec.Policies)
	}
}

func TestLoadPolicyApplyRequestRequiresName(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "policy.yaml")
	if err := os.WriteFile(path, []byte(`
policies:
  - permission: allow
    operations: [GET]
`), 0o600); err != nil {
		t.Fatalf("write policy file: %v", err)
	}

	if _, err := loadPolicyApplyRequest(path, ""); err == nil {
		t.Fatalf("expected missing name error")
	}
}
