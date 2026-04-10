package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestBuildDeployPayloadFromSourceFilesIncludesGovernanceFields(t *testing.T) {
	cwd := t.TempDir()
	sourcePath := filepath.Join(cwd, "agent.py")
	requirementsPath := filepath.Join(cwd, "requirements.txt")
	if err := os.WriteFile(sourcePath, []byte("print('hello')"), 0o600); err != nil {
		t.Fatalf("write source file: %v", err)
	}
	if err := os.WriteFile(requirementsPath, []byte("runagents>=1.3.1\n"), 0o600); err != nil {
		t.Fatalf("write requirements file: %v", err)
	}

	payload, err := buildDeployPayload(deployOptions{
		Name:             "billing-agent",
		Files:            []string{sourcePath},
		Tools:            []string{"stripe-api"},
		ModelFlag:        "openai/gpt-4o-mini",
		Policies:         []string{"billing-write-approval"},
		IdentityProvider: "google-oidc",
		RequirementsFile: requirementsPath,
		EntryPoint:       "agent.py",
		Framework:        "langgraph",
	}, cwd)
	if err != nil {
		t.Fatalf("buildDeployPayload: %v", err)
	}

	if payload["agent_name"] != "billing-agent" {
		t.Fatalf("unexpected agent_name: %#v", payload["agent_name"])
	}
	if payload["identity_provider"] != "google-oidc" {
		t.Fatalf("unexpected identity_provider: %#v", payload["identity_provider"])
	}
	policies, ok := payload["policies"].([]string)
	if !ok || len(policies) != 1 || policies[0] != "billing-write-approval" {
		t.Fatalf("unexpected policies payload: %#v", payload["policies"])
	}
	if payload["entry_point"] != "agent.py" || payload["framework"] != "langgraph" {
		t.Fatalf("unexpected source deploy settings: %#v", payload)
	}
	if payload["requirements"] != "runagents>=1.3.1\n" {
		t.Fatalf("unexpected requirements payload: %#v", payload["requirements"])
	}
}

func TestBuildDeployPayloadFromDraft(t *testing.T) {
	payload, err := buildDeployPayload(deployOptions{
		Name:             "payments-agent",
		DraftID:          "draft_payments_v2",
		Policies:         []string{"payments-approval"},
		IdentityProvider: "okta-oidc",
	}, t.TempDir())
	if err != nil {
		t.Fatalf("buildDeployPayload: %v", err)
	}
	if payload["draft_id"] != "draft_payments_v2" {
		t.Fatalf("unexpected draft_id: %#v", payload["draft_id"])
	}
	if _, exists := payload["source_files"]; exists {
		t.Fatalf("did not expect source_files in draft deploy: %#v", payload)
	}
}

func TestBuildDeployPayloadRejectsMultipleSourceModes(t *testing.T) {
	_, err := buildDeployPayload(deployOptions{
		Name:       "broken-agent",
		Files:      []string{"agent.py"},
		DraftID:    "draft-1",
		ArtifactID: "art-1",
	}, t.TempDir())
	if err == nil {
		t.Fatalf("expected source mode validation error")
	}
}

func TestBuildDeployPayloadRejectsSourceOnlyFlagsWithoutFiles(t *testing.T) {
	_, err := buildDeployPayload(deployOptions{
		Name:       "artifact-agent",
		ArtifactID: "art-1",
		Framework:  "langgraph",
	}, t.TempDir())
	if err == nil {
		t.Fatalf("expected framework validation error")
	}
}

func TestParseDeployModelFlagRejectsInvalidFormat(t *testing.T) {
	if _, err := parseDeployModelFlag("gpt-4o-mini"); err == nil {
		t.Fatalf("expected invalid model format error")
	}
}
