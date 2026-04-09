package commands

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// decodeStructuredFile decodes a JSON or YAML file into out.
func decodeStructuredFile(path string, out any) error {
	trimmed := strings.TrimSpace(path)
	if trimmed == "" {
		return fmt.Errorf("file path cannot be empty")
	}

	data, err := os.ReadFile(trimmed)
	if err != nil {
		return fmt.Errorf("failed to read file %q: %w", trimmed, err)
	}
	if err := decodeStructuredData(data, filepath.Ext(trimmed), out); err != nil {
		return fmt.Errorf("failed to decode %q: %w", trimmed, err)
	}
	return nil
}

func decodeStructuredData(data []byte, ext string, out any) error {
	trimmed := bytes.TrimSpace(data)
	if len(trimmed) == 0 {
		return fmt.Errorf("structured document is empty")
	}

	switch strings.ToLower(strings.TrimSpace(ext)) {
	case ".json":
		return json.Unmarshal(trimmed, out)
	case ".yaml", ".yml":
		return yaml.Unmarshal(trimmed, out)
	}

	if err := json.Unmarshal(trimmed, out); err == nil {
		return nil
	}
	if err := yaml.Unmarshal(trimmed, out); err == nil {
		return nil
	}

	return fmt.Errorf("unsupported structured document format %q", ext)
}
