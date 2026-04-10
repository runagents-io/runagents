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

type contextExportFetch struct {
	key  string
	path string
}

var contextExportFetches = []contextExportFetch{
	{key: "agents", path: "/api/agents"},
	{key: "tools", path: "/api/tools"},
	{key: "model_providers", path: "/api/model-providers"},
	{key: "policies", path: "/api/policies"},
	{key: "identity_providers", path: "/api/identity-providers"},
	{key: "approval_connectors", path: "/api/settings/approval-connectors"},
	{key: "approvals", path: "/governance/requests"},
	{key: "deploy_drafts", path: "/api/deploy-drafts"},
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

			serverPayload, serverErr := fetchJSONResource(c, "/api/context/export")
			if payloadMap, ok := serverPayload.(map[string]interface{}); ok && serverErr == nil {
				if err := enrichContextExportPayload(
					func(path string) (any, error) { return fetchJSONResource(c, path) },
					payloadMap,
					strict,
					endpoint,
					namespace,
				); err != nil {
					return err
				}
				return printContextExport(payloadMap)
			}

			payload := newContextExportPayload(endpoint, namespace)
			if serverErr != nil {
				errorsMap := ensureContextExportObject(payload, "errors")
				errorsMap["context_export"] = serverErr.Error()
			}
			if err := enrichContextExportPayload(
				func(path string) (any, error) { return fetchJSONResource(c, path) },
				payload,
				strict,
				endpoint,
				namespace,
			); err != nil {
				return err
			}
			return printContextExport(payload)
		},
	}
	cmd.Flags().BoolVar(&strict, "strict", false, "Fail when any resource cannot be fetched")
	return cmd
}

func newContextExportPayload(endpoint, namespace string) map[string]any {
	return map[string]any{
		"generated_at": time.Now().UTC().Format(time.RFC3339),
		"endpoint":     endpoint,
		"namespace":    namespace,
		"resources":    map[string]any{},
		"errors":       map[string]any{},
		"meta":         map[string]any{},
	}
}

func enrichContextExportPayload(fetch func(string) (any, error), payload map[string]any, strict bool, endpoint, namespace string) error {
	if payload == nil {
		return fmt.Errorf("context export payload cannot be nil")
	}
	if _, exists := payload["generated_at"]; !exists {
		payload["generated_at"] = time.Now().UTC().Format(time.RFC3339)
	}
	if _, exists := payload["endpoint"]; !exists || payload["endpoint"] == "" {
		payload["endpoint"] = endpoint
	}
	if _, exists := payload["namespace"]; !exists || payload["namespace"] == "" {
		payload["namespace"] = namespace
	}

	resources := ensureContextExportObject(payload, "resources")
	errorsMap := ensureContextExportObject(payload, "errors")
	meta := ensureContextExportObject(payload, "meta")

	for _, item := range contextExportFetches {
		if value, exists := resources[item.key]; exists && value != nil {
			if _, counted := meta[item.key+"_count"]; !counted {
				meta[item.key+"_count"] = estimateItemCount(value)
			}
			continue
		}

		value, err := fetch(item.path)
		if err != nil {
			errorsMap[item.key] = err.Error()
			if strict {
				return fmt.Errorf("failed to fetch %s from %s: %w", item.key, item.path, err)
			}
			continue
		}
		resources[item.key] = value
		meta[item.key+"_count"] = estimateItemCount(value)
	}

	if len(errorsMap) == 0 {
		delete(payload, "errors")
	}
	if len(meta) == 0 {
		delete(payload, "meta")
	}

	return nil
}

func ensureContextExportObject(payload map[string]any, key string) map[string]any {
	if existing, ok := payload[key]; ok {
		switch typed := existing.(type) {
		case map[string]any:
			return typed
		case map[string]string:
			out := make(map[string]any, len(typed))
			for nestedKey, value := range typed {
				out[nestedKey] = value
			}
			payload[key] = out
			return out
		}
	}
	out := map[string]any{}
	payload[key] = out
	return out
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
