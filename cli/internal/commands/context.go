package commands

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/runagents/runagents/cli/internal/client"
	"github.com/spf13/cobra"
)

type contextExportResult struct {
	GeneratedAt string                 `json:"generated_at"`
	Endpoint    string                 `json:"endpoint"`
	Namespace   string                 `json:"namespace"`
	Resources   map[string]any         `json:"resources"`
	Errors      map[string]string      `json:"errors,omitempty"`
	Meta        map[string]interface{} `json:"meta,omitempty"`
}

func newContextCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "context",
		Short: "Export workspace context for external assistants",
	}

	cmd.AddCommand(newContextExportCmd())
	return cmd
}

func newContextExportCmd() *cobra.Command {
	var strict bool
	cmd := &cobra.Command{
		Use:   "export",
		Short: "Export workspace snapshot (agents/tools/models/approvals/drafts)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			endpoint, _, namespace, err := resolvedAPISettings()
			if err != nil {
				return err
			}

			// Prefer server-side aggregate export when available.
			serverPayload, serverErr := fetchJSONResource(c, "/api/context/export")
			if serverErr == nil {
				if payloadMap, ok := serverPayload.(map[string]interface{}); ok {
					if _, exists := payloadMap["endpoint"]; !exists {
						payloadMap["endpoint"] = endpoint
					}
				}
				if strict && contextExportErrorCount(serverPayload) > 0 {
					return fmt.Errorf("context export includes resource errors; rerun without --strict to inspect partial payload")
				}
				return printContextExport(serverPayload)
			}

			result := contextExportResult{
				GeneratedAt: time.Now().UTC().Format(time.RFC3339),
				Endpoint:    endpoint,
				Namespace:   namespace,
				Resources:   map[string]any{},
				Errors:      map[string]string{},
				Meta:        map[string]interface{}{},
			}
			result.Errors["context_export"] = serverErr.Error()

			fetches := []struct {
				key  string
				path string
			}{
				{key: "agents", path: "/api/agents"},
				{key: "tools", path: "/api/tools"},
				{key: "model_providers", path: "/api/model-providers"},
				{key: "approvals", path: "/governance/requests"},
				{key: "deploy_drafts", path: "/api/deploy-drafts"},
			}

			for _, item := range fetches {
				value, fetchErr := fetchJSONResource(c, item.path)
				if fetchErr != nil {
					result.Errors[item.key] = fetchErr.Error()
					if strict {
						return fmt.Errorf("failed to fetch %s from %s: %w", item.key, item.path, fetchErr)
					}
					continue
				}
				result.Resources[item.key] = value
				result.Meta[item.key+"_count"] = estimateItemCount(value)
			}

			if len(result.Errors) == 0 {
				result.Errors = nil
			}
			return printContextExport(result)
		},
	}
	cmd.Flags().BoolVar(&strict, "strict", false, "Fail when any resource cannot be fetched")
	return cmd
}

func fetchJSONResource(c *client.Client, path string) (any, error) {
	data, err := c.Get(path)
	if err != nil {
		return nil, err
	}
	return decodeJSONBody(data)
}

func decodeJSONBody(data []byte) (any, error) {
	var out any
	if err := json.Unmarshal(data, &out); err != nil {
		return nil, fmt.Errorf("failed to decode JSON response: %w", err)
	}
	return out, nil
}

func estimateItemCount(v any) int {
	switch typed := v.(type) {
	case []interface{}:
		return len(typed)
	case map[string]interface{}:
		return len(typed)
	default:
		return 0
	}
}

func contextExportErrorCount(payload any) int {
	asMap, ok := payload.(map[string]interface{})
	if !ok {
		return 0
	}
	raw, ok := asMap["errors"]
	if !ok || raw == nil {
		return 0
	}
	switch typed := raw.(type) {
	case map[string]interface{}:
		return len(typed)
	case map[string]string:
		return len(typed)
	default:
		return 0
	}
}

func printContextExport(payload any) error {
	if isJSONOutput() {
		raw, err := json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("failed to encode context export: %w", err)
		}
		fmt.Println(string(raw))
		return nil
	}

	pretty, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to encode context export: %w", err)
	}
	fmt.Println(string(pretty))
	return nil
}
