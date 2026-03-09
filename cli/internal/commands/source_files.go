package commands

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func readSourceFiles(paths []string, cwd string) (map[string]string, error) {
	files := make(map[string]string, len(paths))
	for _, inputPath := range paths {
		trimmed := strings.TrimSpace(inputPath)
		if trimmed == "" {
			return nil, fmt.Errorf("file path cannot be empty")
		}

		data, err := os.ReadFile(trimmed)
		if err != nil {
			return nil, fmt.Errorf("failed to read file %q: %w", trimmed, err)
		}

		key := sourceFileKey(trimmed, cwd)
		if _, exists := files[key]; exists {
			return nil, fmt.Errorf("duplicate source file key %q; rename one file or pass distinct paths", key)
		}
		files[key] = string(data)
	}
	return files, nil
}

func sourceFileKey(path, cwd string) string {
	cleaned := filepath.Clean(strings.TrimSpace(path))
	if cleaned == "." || cleaned == "" {
		return filepath.Base(path)
	}

	key := cleaned
	if filepath.IsAbs(cleaned) {
		key = filepath.Base(cleaned)
		if rel, err := filepath.Rel(cwd, cleaned); err == nil && rel != "." && !isPathOutsideBase(rel) {
			key = rel
		}
	} else {
		key = strings.TrimPrefix(cleaned, "."+string(os.PathSeparator))
		if key == "" {
			key = filepath.Base(cleaned)
		}
		if isPathOutsideBase(key) {
			key = filepath.Base(cleaned)
		}
	}

	return filepath.ToSlash(strings.TrimPrefix(key, "./"))
}

func isPathOutsideBase(path string) bool {
	return path == ".." || strings.HasPrefix(path, ".."+string(os.PathSeparator))
}
