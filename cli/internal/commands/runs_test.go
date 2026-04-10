package commands

import (
	"testing"
	"time"
)

func TestFilterRunsAppliesClientSideFiltersSortAndLimit(t *testing.T) {
	now := time.Date(2026, 4, 9, 10, 0, 0, 0, time.UTC)
	runs := []cliRun{
		{ID: "run-1", AgentID: "workspace", UserID: "alice@example.com", ConversationID: "conv-a", UpdatedAt: now.Add(-5 * time.Minute)},
		{ID: "run-2", AgentID: "workspace", UserID: "alice@example.com", ConversationID: "conv-a", UpdatedAt: now.Add(-1 * time.Minute)},
		{ID: "run-3", AgentID: "workspace", UserID: "bob@example.com", ConversationID: "conv-b", UpdatedAt: now.Add(-2 * time.Minute)},
	}

	filtered := filterRuns(runs, runFilters{UserID: "alice@example.com", ConversationID: "conv-a", Limit: 1})
	if len(filtered) != 1 {
		t.Fatalf("expected one run, got %d", len(filtered))
	}
	if filtered[0].ID != "run-2" {
		t.Fatalf("expected newest matching run, got %q", filtered[0].ID)
	}
}

func TestFilterRunEventsAppliesTypeAndTailLimit(t *testing.T) {
	events := []cliRunEvent{
		{Seq: 1, Type: "TOOL_REQUEST"},
		{Seq: 2, Type: "APPROVAL_REQUIRED"},
		{Seq: 3, Type: "APPROVAL_REQUIRED"},
		{Seq: 4, Type: "COMPLETED"},
	}

	filtered := filterRunEvents(events, runEventFilters{Type: "approval_required", Limit: 1})
	if len(filtered) != 1 {
		t.Fatalf("expected one event, got %d", len(filtered))
	}
	if filtered[0].Seq != 3 {
		t.Fatalf("expected latest matching event, got seq=%d", filtered[0].Seq)
	}
}

func TestBuildRunTimelineFallsBackToRunStatusWithoutEvents(t *testing.T) {
	now := time.Date(2026, 4, 9, 10, 0, 0, 0, time.UTC)
	timeline := buildRunTimeline(cliRun{ID: "run-1", Status: "PAUSED_APPROVAL", UpdatedAt: now}, nil)
	if len(timeline) != 1 {
		t.Fatalf("expected one synthetic timeline entry, got %d", len(timeline))
	}
	if timeline[0].Type != "PAUSED_APPROVAL" {
		t.Fatalf("expected type PAUSED_APPROVAL, got %q", timeline[0].Type)
	}
}

func TestSummarizeRunEventApprovalRequired(t *testing.T) {
	event := cliRunEvent{
		Type: "APPROVAL_REQUIRED",
		Data: map[string]any{
			"tool_id":    "calendar",
			"capability": "create-event",
		},
	}

	summary := summarizeRunEvent(event)
	if summary != "Approval required for calendar (create-event)" {
		t.Fatalf("unexpected summary: %q", summary)
	}
}

func TestSummarizeToolRequestEvent(t *testing.T) {
	event := cliRunEvent{
		Type: "TOOL_REQUEST",
		Data: map[string]any{
			"tool_id":     "calendar",
			"tool_method": "POST",
			"tool_url":    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
		},
	}

	summary := summarizeToolRequestEvent(event)
	if summary != "Called calendar POST https://www.googleapis.com/calendar/v3/calendars/primary/events" {
		t.Fatalf("unexpected summary: %q", summary)
	}
}

func TestIsTerminalRunStatus(t *testing.T) {
	if !isTerminalRunStatus("COMPLETED") {
		t.Fatalf("expected COMPLETED to be terminal")
	}
	if !isTerminalRunStatus("failed") {
		t.Fatalf("expected FAILED to be terminal")
	}
	if isTerminalRunStatus("PAUSED_APPROVAL") {
		t.Fatalf("expected PAUSED_APPROVAL to be non-terminal")
	}
}
