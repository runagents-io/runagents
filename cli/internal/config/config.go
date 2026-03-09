package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const (
	AssistantModeExternal  = "external"
	AssistantModeRunAgents = "runagents"
	AssistantModeOff       = "off"
)

// Config holds the CLI configuration.
type Config struct {
	Endpoint      string `json:"endpoint"`
	APIKey        string `json:"api_key"`
	Namespace     string `json:"namespace"`
	AssistantMode string `json:"assistant_mode"`
}

// configDir returns the path to the runagents config directory.
func configDir() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home directory: %w", err)
	}
	return filepath.Join(home, ".runagents"), nil
}

// configPath returns the path to the config file.
func configPath() (string, error) {
	dir, err := configDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, "config.json"), nil
}

// Load reads the config from ~/.runagents/config.json.
// If the file does not exist, it returns a default config.
func Load() (*Config, error) {
	path, err := configPath()
	if err != nil {
		return nil, err
	}

	defaultCfg := &Config{
		Endpoint:      "http://localhost:8092",
		Namespace:     "default",
		AssistantMode: AssistantModeExternal,
	}

	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			applyEnvOverrides(defaultCfg)
			normalizedMode, normalizeErr := NormalizeAssistantMode(defaultCfg.AssistantMode)
			if normalizeErr != nil {
				return nil, normalizeErr
			}
			defaultCfg.AssistantMode = normalizedMode
			return defaultCfg, nil
		}
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var cfg Config
	if err := json.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}
	if cfg.Endpoint == "" {
		cfg.Endpoint = defaultCfg.Endpoint
	}
	if cfg.Namespace == "" {
		cfg.Namespace = defaultCfg.Namespace
	}
	if cfg.AssistantMode == "" {
		cfg.AssistantMode = defaultCfg.AssistantMode
	}
	applyEnvOverrides(&cfg)
	normalizedMode, err := NormalizeAssistantMode(cfg.AssistantMode)
	if err != nil {
		return nil, err
	}
	cfg.AssistantMode = normalizedMode
	return &cfg, nil
}

// Save writes the config to ~/.runagents/config.json.
func Save(cfg *Config) error {
	if cfg == nil {
		return fmt.Errorf("config is required")
	}
	normalizedMode, err := NormalizeAssistantMode(cfg.AssistantMode)
	if err != nil {
		return err
	}
	cfg.AssistantMode = normalizedMode

	dir, err := configDir()
	if err != nil {
		return err
	}

	if err := os.MkdirAll(dir, 0700); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	path, err := configPath()
	if err != nil {
		return err
	}

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(path, data, 0600); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}
	return nil
}

func applyEnvOverrides(cfg *Config) {
	if cfg == nil {
		return
	}
	if endpoint := os.Getenv("RUNAGENTS_ENDPOINT"); endpoint != "" {
		cfg.Endpoint = endpoint
	}
	if apiKey := os.Getenv("RUNAGENTS_API_KEY"); apiKey != "" {
		cfg.APIKey = apiKey
	}
	if namespace := os.Getenv("RUNAGENTS_NAMESPACE"); namespace != "" {
		cfg.Namespace = namespace
	}
	if mode := os.Getenv("RUNAGENTS_ASSISTANT_MODE"); mode != "" {
		cfg.AssistantMode = mode
	}
}

func NormalizeAssistantMode(mode string) (string, error) {
	value := strings.ToLower(strings.TrimSpace(mode))
	if value == "" {
		return AssistantModeExternal, nil
	}
	switch value {
	case AssistantModeExternal, AssistantModeRunAgents, AssistantModeOff:
		return value, nil
	default:
		return "", fmt.Errorf("invalid assistant-mode %q; valid values: %s, %s, %s", mode, AssistantModeExternal, AssistantModeRunAgents, AssistantModeOff)
	}
}
