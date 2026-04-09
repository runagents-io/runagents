package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestResolveCatalogLLMConfigsDefaultsToOpenAIForBareModel(t *testing.T) {
	configs, err := resolveCatalogLLMConfigs("gpt-4.1", "")
	if err != nil {
		t.Fatalf("resolveCatalogLLMConfigs: %v", err)
	}
	if len(configs) != 1 {
		t.Fatalf("expected one config, got %d", len(configs))
	}
	if configs[0]["provider"] != "openai" || configs[0]["model"] != "gpt-4.1" {
		t.Fatalf("unexpected config: %#v", configs[0])
	}
}

func TestBuildCatalogDeployPayloadUsesManifestDefaults(t *testing.T) {
	manifest := &catalogManifest{
		ID:           "google-workspace-assistant-agent",
		DefaultModel: "gpt-4.1",
		DeploymentTemplate: catalogDeploymentTemplate{
			AgentName:        "google-workspace-assistant-agent",
			SystemPrompt:     "You are a Google Workspace assistant.",
			RequiredTools:    []string{"email", "calendar"},
			Policies:         []string{"workspace-write-approval"},
			IdentityProvider: "google-oidc",
			SourceFiles: map[string]string{
				"src/agent.py": "print('hello')",
			},
		},
	}

	payload, err := buildCatalogDeployPayload(manifest, catalogDeployOptions{})
	if err != nil {
		t.Fatalf("buildCatalogDeployPayload: %v", err)
	}
	if payload["agent_name"] != "google-workspace-assistant-agent" {
		t.Fatalf("unexpected agent_name: %#v", payload["agent_name"])
	}
	llmConfigs, ok := payload["llm_configs"].([]map[string]string)
	if !ok || len(llmConfigs) != 1 {
		t.Fatalf("expected llm_configs payload, got %#v", payload["llm_configs"])
	}
	if llmConfigs[0]["provider"] != "openai" || llmConfigs[0]["model"] != "gpt-4.1" {
		t.Fatalf("unexpected llm config: %#v", llmConfigs[0])
	}
}

func TestWriteCatalogTemplateWritesSourceFilesAndManifest(t *testing.T) {
	tmp := t.TempDir()
	manifest := &catalogManifest{
		ID: "test-agent",
		DeploymentTemplate: catalogDeploymentTemplate{
			SourceFiles: map[string]string{
				"src/agent.py": "print('hello')",
				"src/utils.py": "def x(): pass\n",
				"README.local": "notes",
			},
		},
	}

	summary, err := writeCatalogTemplate(filepath.Join(tmp, "agent"), manifest, false)
	if err != nil {
		t.Fatalf("writeCatalogTemplate: %v", err)
	}
	if _, err := os.Stat(filepath.Join(summary.TargetDir, "src", "agent.py")); err != nil {
		t.Fatalf("expected source file to exist: %v", err)
	}
	if _, err := os.Stat(filepath.Join(summary.TargetDir, catalogManifestFilename)); err != nil {
		t.Fatalf("expected manifest file to exist: %v", err)
	}
}

func TestWriteCatalogTemplateRefusesOverwriteWithoutForce(t *testing.T) {
	tmp := t.TempDir()
	target := filepath.Join(tmp, "agent")
	if err := os.MkdirAll(filepath.Join(target, "src"), 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(target, "src", "agent.py"), []byte("existing"), 0o644); err != nil {
		t.Fatalf("write existing: %v", err)
	}

	manifest := &catalogManifest{
		ID: "test-agent",
		DeploymentTemplate: catalogDeploymentTemplate{
			SourceFiles: map[string]string{"src/agent.py": "print('new')"},
		},
	}
	if _, err := writeCatalogTemplate(target, manifest, false); err == nil {
		t.Fatalf("expected overwrite protection error")
	}
}

func TestCatalogListQueryIncludesFilters(t *testing.T) {
	query := catalogListQuery(
		"google",
		[]string{"Enterprise Productivity"},
		[]string{"Gmail"},
		[]string{"calendar"},
		[]string{"approval-ready"},
		2,
		50,
	)
	if got := query.Get("search"); got != "google" {
		t.Fatalf("expected search query, got %q", got)
	}
	if got := query.Get("category"); got != "Enterprise Productivity" {
		t.Fatalf("expected category query, got %q", got)
	}
	if got := query.Get("tag"); got != "Gmail" {
		t.Fatalf("expected tag query, got %q", got)
	}
	if got := query.Get("integration"); got != "calendar" {
		t.Fatalf("expected integration query, got %q", got)
	}
	if got := query.Get("governance"); got != "approval-ready" {
		t.Fatalf("expected governance query, got %q", got)
	}
	if got := query.Get("page"); got != "2" {
		t.Fatalf("expected page query, got %q", got)
	}
	if got := query.Get("page_size"); got != "50" {
		t.Fatalf("expected page_size query, got %q", got)
	}
}
