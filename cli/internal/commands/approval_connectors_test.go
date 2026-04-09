package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadApprovalConnectorApplyRequest(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "connector.yaml")
	if err := os.WriteFile(path, []byte(`
name: secops-slack
type: slack
endpoint: C12345
headers:
  X-Slack-Bot-Token: xoxb-1
timeout_seconds: 15
`), 0o600); err != nil {
		t.Fatalf("write connector file: %v", err)
	}

	req, err := loadApprovalConnectorApplyRequest(path)
	if err != nil {
		t.Fatalf("loadApprovalConnectorApplyRequest: %v", err)
	}
	if req.Name != "secops-slack" || req.Type != "slack" || req.Endpoint != "C12345" {
		t.Fatalf("unexpected connector request: %#v", req)
	}
	if req.TimeoutSeconds == nil || *req.TimeoutSeconds != 15 {
		t.Fatalf("expected timeout_seconds=15, got %#v", req.TimeoutSeconds)
	}
}

func TestLoadApprovalConnectorApplyRequestRequiresIDOrName(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "connector.json")
	if err := os.WriteFile(path, []byte(`{"type":"webhook","endpoint":"https://approvals.example.com/hook"}`), 0o600); err != nil {
		t.Fatalf("write connector file: %v", err)
	}

	if _, err := loadApprovalConnectorApplyRequest(path); err == nil {
		t.Fatalf("expected missing id/name error")
	}
}

func TestResolveApprovalConnectorTarget(t *testing.T) {
	connectors := []cliApprovalConnector{
		{ID: "c1", Name: "secops-slack", Type: "slack"},
		{ID: "c2", Name: "finance-webhook", Type: "webhook"},
	}

	target, err := resolveApprovalConnectorTarget(connectors, cliApprovalConnectorApplyRequest{ID: "c2"})
	if err != nil {
		t.Fatalf("resolve by id: %v", err)
	}
	if target == nil || target.ID != "c2" {
		t.Fatalf("expected connector c2, got %#v", target)
	}

	target, err = resolveApprovalConnectorTarget(connectors, cliApprovalConnectorApplyRequest{Name: "secops-slack"})
	if err != nil {
		t.Fatalf("resolve by name: %v", err)
	}
	if target == nil || target.ID != "c1" {
		t.Fatalf("expected connector c1, got %#v", target)
	}
}

func TestResolveApprovalConnectorTargetRejectsDuplicateName(t *testing.T) {
	connectors := []cliApprovalConnector{
		{ID: "c1", Name: "shared-name"},
		{ID: "c2", Name: "shared-name"},
	}
	if _, err := resolveApprovalConnectorTarget(connectors, cliApprovalConnectorApplyRequest{Name: "shared-name"}); err == nil {
		t.Fatalf("expected duplicate name error")
	}
}

func TestBuildApprovalConnectorCreateRequiresEndpoint(t *testing.T) {
	_, err := buildApprovalConnectorCreate(cliApprovalConnectorApplyRequest{Name: "secops"})
	if err == nil {
		t.Fatalf("expected endpoint validation error")
	}
}

func TestBuildApprovalConnectorPatchIncludesProvidedFields(t *testing.T) {
	enabled := false
	timeout := 20
	headers := map[string]string{"Authorization": "Bearer abc"}
	patch := buildApprovalConnectorPatch(cliApprovalConnectorApplyRequest{
		Name:              "secops",
		Type:              "webhook",
		Endpoint:          "https://approvals.example.com/hook",
		Headers:           headers,
		Enabled:           &enabled,
		TimeoutSeconds:    &timeout,
		SlackSecurityMode: "strict",
	})

	if patch.Name == nil || *patch.Name != "secops" {
		t.Fatalf("expected name patch, got %#v", patch.Name)
	}
	if patch.Headers == nil || (*patch.Headers)["Authorization"] != "Bearer abc" {
		t.Fatalf("expected headers patch, got %#v", patch.Headers)
	}
	if patch.Enabled == nil || *patch.Enabled {
		t.Fatalf("expected enabled=false, got %#v", patch.Enabled)
	}
	if patch.TimeoutSeconds == nil || *patch.TimeoutSeconds != 20 {
		t.Fatalf("expected timeout=20, got %#v", patch.TimeoutSeconds)
	}
	if patch.SlackSecurity == nil || *patch.SlackSecurity != "strict" {
		t.Fatalf("expected slack security strict, got %#v", patch.SlackSecurity)
	}
}

func TestBuildApprovalConnectorTestRequest(t *testing.T) {
	connector := cliApprovalConnector{
		Type:              "slack",
		Endpoint:          "C12345",
		Headers:           map[string]string{"X-Slack-Bot-Token": "xoxb-1"},
		TimeoutSeconds:    30,
		SlackSecurityMode: "compat",
	}
	request := buildApprovalConnectorTestRequest(connector)
	if request.Type != "slack" || request.Endpoint != "C12345" {
		t.Fatalf("unexpected test request: %#v", request)
	}
	if request.TimeoutSeconds == nil || *request.TimeoutSeconds != 30 {
		t.Fatalf("expected timeout_seconds=30, got %#v", request.TimeoutSeconds)
	}
}
