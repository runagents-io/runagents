package commands

import "testing"

func TestNormalizeApprovalScope(t *testing.T) {
	tests := []struct {
		name      string
		scope     string
		duration  string
		wantScope string
		wantErr   bool
	}{
		{name: "default empty", scope: "", duration: "", wantScope: ""},
		{name: "duration implies window", scope: "", duration: "4h", wantScope: "agent_user_ttl"},
		{name: "once", scope: "once", wantScope: "once"},
		{name: "run", scope: "run", wantScope: "run"},
		{name: "window alias", scope: "window", wantScope: "agent_user_ttl"},
		{name: "ttl alias", scope: "ttl", wantScope: "agent_user_ttl"},
		{name: "internal ttl", scope: "agent_user_ttl", wantScope: "agent_user_ttl"},
		{name: "duration with once rejected", scope: "once", duration: "1h", wantErr: true},
		{name: "duration with run rejected", scope: "run", duration: "1h", wantErr: true},
		{name: "unknown rejected", scope: "forever", wantErr: true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := normalizeApprovalScope(tt.scope, tt.duration)
			if tt.wantErr {
				if err == nil {
					t.Fatalf("expected error, got nil")
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if got != tt.wantScope {
				t.Fatalf("expected scope %q, got %q", tt.wantScope, got)
			}
		})
	}
}

func TestBuildApprovalDecision(t *testing.T) {
	decision, err := buildApprovalDecision("", "")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if decision != nil {
		t.Fatalf("expected nil decision, got %#v", decision)
	}

	decision, err = buildApprovalDecision("window", "4h")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if decision == nil {
		t.Fatalf("expected decision")
	}
	if decision.Scope != "agent_user_ttl" || decision.Duration != "4h" {
		t.Fatalf("unexpected decision: %#v", decision)
	}
}
