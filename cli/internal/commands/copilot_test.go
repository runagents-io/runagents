package commands

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestShouldUseCurrentFolderDeployAssist(t *testing.T) {
	tests := []struct {
		prompt string
		want   bool
	}{
		{prompt: "deploy this folder", want: true},
		{prompt: "Please deploy current folder as billing-agent", want: true},
		{prompt: "deploy draft draft-1 as billing-agent", want: false},
		{prompt: "list my tools", want: false},
	}
	for _, tc := range tests {
		got := shouldUseCurrentFolderDeployAssist(tc.prompt)
		if got != tc.want {
			t.Fatalf("prompt %q expected %v, got %v", tc.prompt, tc.want, got)
		}
	}
}

func TestSanitizeAgentName(t *testing.T) {
	got := sanitizeAgentName("Billing Agent_v2!!")
	if got != "billing-agent-v2" {
		t.Fatalf("expected billing-agent-v2, got %q", got)
	}
}

func TestInferAgentNameFromPromptOrDir(t *testing.T) {
	got := inferAgentNameFromPromptOrDir("deploy this folder as payments-core", "/tmp/my-repo")
	if got != "payments-core" {
		t.Fatalf("expected payments-core from prompt, got %q", got)
	}

	fallback := inferAgentNameFromPromptOrDir("deploy this folder", "/tmp/my-repo")
	if fallback != "my-repo-agent" {
		t.Fatalf("expected fallback my-repo-agent, got %q", fallback)
	}
}

func TestCollectLocalSourceFilesIncludesCommonStacks(t *testing.T) {
	tmp := t.TempDir()

	mustMkdirAll(t, filepath.Join(tmp, "src"))
	mustMkdirAll(t, filepath.Join(tmp, "node_modules"))

	mustWriteFile(t, filepath.Join(tmp, "main.py"), "print('ok')")
	mustWriteFile(t, filepath.Join(tmp, "src", "index.ts"), "export const x = 1;")
	mustWriteFile(t, filepath.Join(tmp, "go.mod"), "module example.com/test")
	mustWriteFile(t, filepath.Join(tmp, "Dockerfile"), "FROM python:3.12")
	mustWriteFile(t, filepath.Join(tmp, "node_modules", "ignored.js"), "console.log('ignore');")

	files, err := collectLocalSourceFiles(tmp)
	if err != nil {
		t.Fatalf("collectLocalSourceFiles: %v", err)
	}

	expected := []string{"main.py", "src/index.ts", "go.mod", "Dockerfile"}
	for _, path := range expected {
		if _, ok := files[path]; !ok {
			t.Fatalf("expected %s to be included", path)
		}
	}
	if _, ok := files["node_modules/ignored.js"]; ok {
		t.Fatalf("expected node_modules file to be excluded")
	}
}

func TestCollectLocalSourceFilesSkipsOversizedFile(t *testing.T) {
	tmp := t.TempDir()
	mustWriteFile(t, filepath.Join(tmp, "small.py"), "print('small')")
	mustWriteFile(t, filepath.Join(tmp, "large.py"), strings.Repeat("x", copilotMaxFileSize+1))

	files, err := collectLocalSourceFiles(tmp)
	if err != nil {
		t.Fatalf("collectLocalSourceFiles: %v", err)
	}
	if _, ok := files["small.py"]; !ok {
		t.Fatalf("expected small.py to be included")
	}
	if _, ok := files["large.py"]; ok {
		t.Fatalf("expected oversized file to be skipped")
	}
}

func TestShouldProceedWithDeployAssistAssumeYes(t *testing.T) {
	ok, err := shouldProceedWithDeployAssist(false, true, nil, nil)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if !ok {
		t.Fatalf("expected confirmation to proceed when assumeYes=true")
	}
}

func TestShouldProceedWithDeployAssistNonInteractiveRequiresFlag(t *testing.T) {
	ok, err := shouldProceedWithDeployAssist(false, false, nil, nil)
	if err == nil {
		t.Fatalf("expected error for non-interactive without --yes")
	}
	if ok {
		t.Fatalf("expected proceed=false for non-interactive without --yes")
	}
}

func TestShouldProceedWithDeployAssistInteractiveYes(t *testing.T) {
	var out bytes.Buffer
	ok, err := shouldProceedWithDeployAssist(true, false, strings.NewReader("yes\n"), &out)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if !ok {
		t.Fatalf("expected proceed=true for yes answer")
	}
	if !strings.Contains(out.String(), "Proceed?") {
		t.Fatalf("expected confirmation prompt output")
	}
}

func TestShouldProceedWithDeployAssistInteractiveNo(t *testing.T) {
	ok, err := shouldProceedWithDeployAssist(true, false, strings.NewReader("no\n"), &bytes.Buffer{})
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if ok {
		t.Fatalf("expected proceed=false for no answer")
	}
}

func TestExtractHTTPStatus(t *testing.T) {
	code := extractHTTPStatus(errors.New("API error (HTTP 403): forbidden"))
	if code != 403 {
		t.Fatalf("expected 403, got %d", code)
	}
	if got := extractHTTPStatus(errors.New("some random error")); got != 0 {
		t.Fatalf("expected 0 for unparsable error, got %d", got)
	}
}

func TestEnsureCopilotEnabledByAssistantMode(t *testing.T) {
	original, had := os.LookupEnv("RUNAGENTS_ASSISTANT_MODE")
	defer func() {
		if had {
			_ = os.Setenv("RUNAGENTS_ASSISTANT_MODE", original)
			return
		}
		_ = os.Unsetenv("RUNAGENTS_ASSISTANT_MODE")
	}()

	_ = os.Setenv("RUNAGENTS_ASSISTANT_MODE", "runagents")
	if err := ensureCopilotEnabled(); err != nil {
		t.Fatalf("expected copilot to be enabled in runagents mode: %v", err)
	}

	_ = os.Setenv("RUNAGENTS_ASSISTANT_MODE", "external")
	if err := ensureCopilotEnabled(); err == nil {
		t.Fatalf("expected copilot to be disabled in external mode")
	}
}

func mustWriteFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func mustMkdirAll(t *testing.T, path string) {
	t.Helper()
	if err := os.MkdirAll(path, 0755); err != nil {
		t.Fatalf("mkdir %s: %v", path, err)
	}
}
