package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadActionPlanFile(t *testing.T) {
	tmp := t.TempDir()
	planPath := filepath.Join(tmp, "plan.json")
	if err := os.WriteFile(planPath, []byte(`{"plan_id":"p1","actions":[{"id":"a1"}]}`), 0644); err != nil {
		t.Fatalf("write plan: %v", err)
	}

	payload, err := loadActionPlanFile(planPath)
	if err != nil {
		t.Fatalf("expected success, got: %v", err)
	}
	if payload["plan_id"] != "p1" {
		t.Fatalf("expected plan_id p1, got %#v", payload["plan_id"])
	}
}

func TestLoadActionPlanFileInvalidJSON(t *testing.T) {
	tmp := t.TempDir()
	planPath := filepath.Join(tmp, "invalid.json")
	if err := os.WriteFile(planPath, []byte(`{`), 0644); err != nil {
		t.Fatalf("write plan: %v", err)
	}
	if _, err := loadActionPlanFile(planPath); err == nil {
		t.Fatalf("expected invalid JSON error")
	}
}

func TestLoadActionPlanFileMissingPath(t *testing.T) {
	if _, err := loadActionPlanFile(""); err == nil {
		t.Fatalf("expected missing path error")
	}
}
