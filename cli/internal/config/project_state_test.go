package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestProjectStateRoundTrip(t *testing.T) {
	tmp := t.TempDir()
	initial := &ProjectState{
		SessionID:        "cps_test",
		LastPrompt:       "deploy this folder",
		LastResponse:     "staged",
		PendingActionIDs: []string{"act_1", "act_2"},
		UpdatedAt:        time.Now().UTC(),
	}

	if err := SaveProjectState(tmp, initial); err != nil {
		t.Fatalf("save state: %v", err)
	}

	loaded, err := LoadProjectState(tmp)
	if err != nil {
		t.Fatalf("load state: %v", err)
	}

	if loaded.SessionID != initial.SessionID {
		t.Fatalf("expected session %q, got %q", initial.SessionID, loaded.SessionID)
	}
	if len(loaded.PendingActionIDs) != 2 {
		t.Fatalf("expected 2 pending action IDs, got %d", len(loaded.PendingActionIDs))
	}

	stateInfo, err := os.Stat(filepath.Join(tmp, ".runagents", "state.json"))
	if err != nil {
		t.Fatalf("stat state file: %v", err)
	}
	if got := stateInfo.Mode().Perm(); got != 0600 {
		t.Fatalf("expected state file mode 0600, got %o", got)
	}

	dirInfo, err := os.Stat(filepath.Join(tmp, ".runagents"))
	if err != nil {
		t.Fatalf("stat .runagents dir: %v", err)
	}
	if got := dirInfo.Mode().Perm(); got != 0700 {
		t.Fatalf("expected .runagents dir mode 0700, got %o", got)
	}
}

func TestProjectStateResetRemovesFiles(t *testing.T) {
	tmp := t.TempDir()
	if err := SaveProjectState(tmp, &ProjectState{SessionID: "cps_reset"}); err != nil {
		t.Fatalf("save state: %v", err)
	}
	if err := SaveProjectMemory(tmp, MemorySnapshot{
		CurrentGoal: "test",
		SessionID:   "cps_reset",
		UpdatedAt:   time.Now().UTC(),
	}); err != nil {
		t.Fatalf("save memory: %v", err)
	}

	if err := ResetProjectState(tmp); err != nil {
		t.Fatalf("reset state: %v", err)
	}

	if _, err := os.Stat(filepath.Join(tmp, ".runagents", "state.json")); !os.IsNotExist(err) {
		t.Fatalf("expected state file to be removed")
	}
	if _, err := os.Stat(filepath.Join(tmp, ".runagents", "memory.md")); !os.IsNotExist(err) {
		t.Fatalf("expected memory file to be removed")
	}
}

func TestSaveProjectMemoryWritesSections(t *testing.T) {
	tmp := t.TempDir()
	err := SaveProjectMemory(tmp, MemorySnapshot{
		CurrentGoal:          "Deploy current repo",
		SessionID:            "cps_memory",
		RecentSummary:        "one action staged",
		PendingActionIDs:     []string{"act_1"},
		NextSuggestedCommand: "runagents copilot confirm act_1",
		UpdatedAt:            time.Now().UTC(),
	})
	if err != nil {
		t.Fatalf("save memory: %v", err)
	}

	raw, err := os.ReadFile(filepath.Join(tmp, ".runagents", "memory.md"))
	if err != nil {
		t.Fatalf("read memory file: %v", err)
	}
	content := string(raw)
	if !strings.Contains(content, "## Current Goal") {
		t.Fatalf("expected current goal section in memory.md")
	}
	if !strings.Contains(content, "runagents copilot confirm act_1") {
		t.Fatalf("expected next command hint in memory.md")
	}

	memoryInfo, err := os.Stat(filepath.Join(tmp, ".runagents", "memory.md"))
	if err != nil {
		t.Fatalf("stat memory file: %v", err)
	}
	if got := memoryInfo.Mode().Perm(); got != 0600 {
		t.Fatalf("expected memory file mode 0600, got %o", got)
	}
}
