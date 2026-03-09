package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// ProjectState stores per-repository CLI session continuity.
type ProjectState struct {
	SessionID        string    `json:"session_id,omitempty"`
	LastPrompt       string    `json:"last_prompt,omitempty"`
	LastResponse     string    `json:"last_response,omitempty"`
	PendingActionIDs []string  `json:"pending_action_ids,omitempty"`
	UpdatedAt        time.Time `json:"updated_at"`
}

// MemorySnapshot is rendered to .runagents/memory.md for humans/agents.
type MemorySnapshot struct {
	CurrentGoal          string
	SessionID            string
	RecentSummary        string
	PendingActionIDs     []string
	NextSuggestedCommand string
	UpdatedAt            time.Time
}

func projectDataDir(cwd string) string {
	base := strings.TrimSpace(cwd)
	if base == "" {
		base = "."
	}
	return filepath.Join(base, ".runagents")
}

func projectStatePath(cwd string) string {
	return filepath.Join(projectDataDir(cwd), "state.json")
}

func projectMemoryPath(cwd string) string {
	return filepath.Join(projectDataDir(cwd), "memory.md")
}

// LoadProjectState loads .runagents/state.json from the current project.
// Missing file is treated as empty state.
func LoadProjectState(cwd string) (*ProjectState, error) {
	path := projectStatePath(cwd)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return &ProjectState{}, nil
		}
		return nil, fmt.Errorf("failed to read project state: %w", err)
	}
	var state ProjectState
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, fmt.Errorf("failed to parse project state: %w", err)
	}
	return &state, nil
}

// SaveProjectState writes .runagents/state.json.
func SaveProjectState(cwd string, state *ProjectState) error {
	if state == nil {
		state = &ProjectState{}
	}
	if state.UpdatedAt.IsZero() {
		state.UpdatedAt = time.Now().UTC()
	}
	dir := projectDataDir(cwd)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return fmt.Errorf("failed to create project state dir: %w", err)
	}
	data, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to encode project state: %w", err)
	}
	if err := os.WriteFile(projectStatePath(cwd), data, 0600); err != nil {
		return fmt.Errorf("failed to write project state: %w", err)
	}
	return nil
}

// ResetProjectState removes local state and memory files.
func ResetProjectState(cwd string) error {
	_ = os.Remove(projectStatePath(cwd))
	_ = os.Remove(projectMemoryPath(cwd))
	return nil
}

// SaveProjectMemory writes .runagents/memory.md with a concise session summary.
func SaveProjectMemory(cwd string, snapshot MemorySnapshot) error {
	if snapshot.UpdatedAt.IsZero() {
		snapshot.UpdatedAt = time.Now().UTC()
	}
	dir := projectDataDir(cwd)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return fmt.Errorf("failed to create project memory dir: %w", err)
	}

	lines := []string{
		"# RunAgents CLI Memory",
		"",
		fmt.Sprintf("Updated: %s", snapshot.UpdatedAt.Format(time.RFC3339)),
		"",
		"## Current Goal",
		defaultText(snapshot.CurrentGoal, "(not set)"),
		"",
		"## Session",
		defaultText(snapshot.SessionID, "(none)"),
		"",
		"## Recent Summary",
		defaultText(snapshot.RecentSummary, "(none)"),
		"",
		"## Pending Actions",
	}
	if len(snapshot.PendingActionIDs) == 0 {
		lines = append(lines, "- (none)")
	} else {
		for _, id := range snapshot.PendingActionIDs {
			lines = append(lines, "- "+id)
		}
	}
	lines = append(lines,
		"",
		"## Next Command",
		defaultText(snapshot.NextSuggestedCommand, "(none)"),
		"",
	)

	if err := os.WriteFile(projectMemoryPath(cwd), []byte(strings.Join(lines, "\n")), 0600); err != nil {
		return fmt.Errorf("failed to write project memory: %w", err)
	}
	return nil
}

func defaultText(v, fallback string) string {
	if strings.TrimSpace(v) == "" {
		return fallback
	}
	return strings.TrimSpace(v)
}
