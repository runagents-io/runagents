package config

import "testing"

func TestNormalizeAssistantMode(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		want    string
		wantErr bool
	}{
		{name: "empty defaults to external", input: "", want: AssistantModeExternal},
		{name: "external exact", input: "external", want: AssistantModeExternal},
		{name: "runagents exact", input: "runagents", want: AssistantModeRunAgents},
		{name: "off exact", input: "off", want: AssistantModeOff},
		{name: "trim and lower", input: "  RUNAGENTS  ", want: AssistantModeRunAgents},
		{name: "invalid", input: "copilot", wantErr: true},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got, err := NormalizeAssistantMode(tc.input)
			if tc.wantErr {
				if err == nil {
					t.Fatalf("expected error for %q", tc.input)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error for %q: %v", tc.input, err)
			}
			if got != tc.want {
				t.Fatalf("expected %q, got %q", tc.want, got)
			}
		})
	}
}

func TestLoadDefaultsAssistantModeFromEnv(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("RUNAGENTS_ASSISTANT_MODE", "runagents")

	cfg, err := Load()
	if err != nil {
		t.Fatalf("expected load to succeed, got error: %v", err)
	}
	if cfg.AssistantMode != AssistantModeRunAgents {
		t.Fatalf("expected assistant mode %q, got %q", AssistantModeRunAgents, cfg.AssistantMode)
	}
}

func TestLoadRejectsInvalidAssistantModeFromEnv(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("RUNAGENTS_ASSISTANT_MODE", "bad-value")

	if _, err := Load(); err == nil {
		t.Fatalf("expected load error for invalid assistant mode")
	}
}
