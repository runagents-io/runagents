package commands

import (
	"testing"
)

func TestEstimateItemCount(t *testing.T) {
	if got := estimateItemCount([]interface{}{1, 2, 3}); got != 3 {
		t.Fatalf("expected 3, got %d", got)
	}
	if got := estimateItemCount(map[string]interface{}{"a": 1, "b": 2}); got != 2 {
		t.Fatalf("expected 2, got %d", got)
	}
	if got := estimateItemCount("unknown"); got != 0 {
		t.Fatalf("expected 0, got %d", got)
	}
}

func TestDecodeJSONBody(t *testing.T) {
	value, err := decodeJSONBody([]byte(`{"items":[1,2]}`))
	if err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}
	parsed, ok := value.(map[string]interface{})
	if !ok {
		t.Fatalf("expected object map, got %T", value)
	}
	if _, ok := parsed["items"]; !ok {
		t.Fatalf("expected items key in parsed response")
	}
}

func TestDecodeJSONBodyInvalid(t *testing.T) {
	if _, err := decodeJSONBody([]byte(`{`)); err == nil {
		t.Fatalf("expected decode error for invalid JSON")
	}
}

func TestContextExportErrorCount(t *testing.T) {
	payload := map[string]interface{}{
		"errors": map[string]interface{}{
			"agents": "failed",
			"tools":  "failed",
		},
	}
	if got := contextExportErrorCount(payload); got != 2 {
		t.Fatalf("expected 2 errors, got %d", got)
	}
	if got := contextExportErrorCount(map[string]interface{}{}); got != 0 {
		t.Fatalf("expected 0 errors, got %d", got)
	}
}
