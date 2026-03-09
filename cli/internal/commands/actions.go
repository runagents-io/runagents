package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
)

type actionValidateResultPayload struct {
	ID             string   `json:"id"`
	Type           string   `json:"type"`
	IdempotencyKey string   `json:"idempotency_key,omitempty"`
	Valid          bool     `json:"valid"`
	Errors         []string `json:"errors,omitempty"`
	ResourceRef    string   `json:"resource_ref,omitempty"`
}

type actionValidateResponsePayload struct {
	PlanID    string                        `json:"plan_id,omitempty"`
	Namespace string                        `json:"namespace"`
	Valid     bool                          `json:"valid"`
	Results   []actionValidateResultPayload `json:"results"`
}

type actionApplyResultPayload struct {
	ID             string `json:"id"`
	Type           string `json:"type"`
	IdempotencyKey string `json:"idempotency_key,omitempty"`
	Status         string `json:"status"`
	ResourceRef    string `json:"resource_ref,omitempty"`
	Error          string `json:"error,omitempty"`
}

type actionApplyResponsePayload struct {
	PlanID       string                     `json:"plan_id,omitempty"`
	Namespace    string                     `json:"namespace"`
	Applied      bool                       `json:"applied"`
	AppliedCount int                        `json:"applied_count"`
	FailedCount  int                        `json:"failed_count"`
	Results      []actionApplyResultPayload `json:"results"`
}

func newActionCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:     "action",
		Aliases: []string{"actions"},
		Short:   "Validate and apply deterministic action plans",
	}

	cmd.AddCommand(newActionValidateCmd())
	cmd.AddCommand(newActionApplyCmd())
	return cmd
}

func newActionValidateCmd() *cobra.Command {
	var filePath string
	cmd := &cobra.Command{
		Use:   "validate",
		Short: "Validate an action plan JSON without applying changes",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			payload, err := loadActionPlanFile(filePath)
			if err != nil {
				return err
			}
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Post("/api/actions/validate", payload)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			return printActionValidateResponse(data)
		},
	}
	cmd.Flags().StringVar(&filePath, "file", "", "Path to action plan JSON file")
	_ = cmd.MarkFlagRequired("file")
	return cmd
}

func newActionApplyCmd() *cobra.Command {
	var filePath string
	cmd := &cobra.Command{
		Use:   "apply",
		Short: "Apply an action plan JSON through governance APIs",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			payload, err := loadActionPlanFile(filePath)
			if err != nil {
				return err
			}
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Post("/api/actions/apply", payload)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			return printActionApplyResponse(data)
		},
	}
	cmd.Flags().StringVar(&filePath, "file", "", "Path to action plan JSON file")
	_ = cmd.MarkFlagRequired("file")
	return cmd
}

func loadActionPlanFile(path string) (map[string]any, error) {
	trimmed := strings.TrimSpace(path)
	if trimmed == "" {
		return nil, fmt.Errorf("file path is required")
	}
	data, err := os.ReadFile(trimmed)
	if err != nil {
		return nil, fmt.Errorf("failed to read %q: %w", trimmed, err)
	}
	var payload map[string]any
	if err := json.Unmarshal(data, &payload); err != nil {
		return nil, fmt.Errorf("invalid JSON in %q: %w", trimmed, err)
	}
	if len(payload) == 0 {
		return nil, fmt.Errorf("action plan file %q is empty", trimmed)
	}
	return payload, nil
}

func printActionValidateResponse(data []byte) error {
	var resp actionValidateResponsePayload
	if err := json.Unmarshal(data, &resp); err != nil {
		return fmt.Errorf("failed to decode action validate response: %w", err)
	}

	validity := "INVALID"
	if resp.Valid {
		validity = "VALID"
	}
	fmt.Printf("Plan:      %s\n", emptyFallback(resp.PlanID, "(none)"))
	fmt.Printf("Namespace: %s\n", emptyFallback(resp.Namespace, "(none)"))
	fmt.Printf("Status:    %s\n", validity)

	for _, result := range resp.Results {
		label := "OK"
		if !result.Valid {
			label = "FAIL"
		}
		fmt.Printf("- [%s] %s (%s)\n", label, emptyFallback(result.ID, "(no-id)"), result.Type)
		if result.ResourceRef != "" {
			fmt.Printf("  resource: %s\n", result.ResourceRef)
		}
		if len(result.Errors) > 0 {
			fmt.Printf("  errors: %s\n", strings.Join(result.Errors, "; "))
		}
	}
	return nil
}

func printActionApplyResponse(data []byte) error {
	var resp actionApplyResponsePayload
	if err := json.Unmarshal(data, &resp); err != nil {
		return fmt.Errorf("failed to decode action apply response: %w", err)
	}

	status := "FAILED"
	if resp.Applied {
		status = "APPLIED"
	}
	fmt.Printf("Plan:         %s\n", emptyFallback(resp.PlanID, "(none)"))
	fmt.Printf("Namespace:    %s\n", emptyFallback(resp.Namespace, "(none)"))
	fmt.Printf("Status:       %s\n", status)
	fmt.Printf("Applied:      %d\n", resp.AppliedCount)
	fmt.Printf("Failed:       %d\n", resp.FailedCount)
	for _, result := range resp.Results {
		fmt.Printf("- [%s] %s (%s)\n", strings.ToUpper(result.Status), emptyFallback(result.ID, "(no-id)"), result.Type)
		if result.ResourceRef != "" {
			fmt.Printf("  resource: %s\n", result.ResourceRef)
		}
		if result.Error != "" {
			fmt.Printf("  error: %s\n", result.Error)
		}
	}
	return nil
}

func emptyFallback(value, fallback string) string {
	if strings.TrimSpace(value) == "" {
		return fallback
	}
	return strings.TrimSpace(value)
}
