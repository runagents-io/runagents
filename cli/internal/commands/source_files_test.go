package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestReadSourceFilesUsesRelativeNestedKeys(t *testing.T) {
	cwd := t.TempDir()
	pathA := filepath.Join(cwd, "src", "main.py")
	pathB := filepath.Join(cwd, "tests", "main.py")

	if err := os.MkdirAll(filepath.Dir(pathA), 0755); err != nil {
		t.Fatalf("mkdir pathA: %v", err)
	}
	if err := os.MkdirAll(filepath.Dir(pathB), 0755); err != nil {
		t.Fatalf("mkdir pathB: %v", err)
	}
	if err := os.WriteFile(pathA, []byte("print('a')"), 0644); err != nil {
		t.Fatalf("write pathA: %v", err)
	}
	if err := os.WriteFile(pathB, []byte("print('b')"), 0644); err != nil {
		t.Fatalf("write pathB: %v", err)
	}

	files, err := readSourceFiles([]string{pathA, pathB}, cwd)
	if err != nil {
		t.Fatalf("readSourceFiles: %v", err)
	}

	if _, ok := files["src/main.py"]; !ok {
		t.Fatalf("expected src/main.py key, got %#v", files)
	}
	if _, ok := files["tests/main.py"]; !ok {
		t.Fatalf("expected tests/main.py key, got %#v", files)
	}
}

func TestReadSourceFilesDetectsDuplicateNormalizedKey(t *testing.T) {
	cwd := t.TempDir()
	pathA := filepath.Join(cwd, "agent.py")
	if err := os.WriteFile(pathA, []byte("print('agent')"), 0644); err != nil {
		t.Fatalf("write pathA: %v", err)
	}

	alias := filepath.Join(cwd, ".", "agent.py")
	_, err := readSourceFiles([]string{pathA, alias}, cwd)
	if err == nil {
		t.Fatalf("expected duplicate key error")
	}
}

func TestSourceFileKeyOutsideBaseFallsBackToBasename(t *testing.T) {
	cwd := t.TempDir()
	key := sourceFileKey("../secret/agent.py", cwd)
	if key != "agent.py" {
		t.Fatalf("expected basename fallback, got %q", key)
	}
}
