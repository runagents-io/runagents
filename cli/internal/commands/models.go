package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

func newModelsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "models",
		Short: "Manage model providers",
	}

	cmd.AddCommand(newModelsListCmd())
	cmd.AddCommand(newModelsGetCmd())
	cmd.AddCommand(newModelsSpendCmd())
	cmd.AddCommand(newModelsCreateCmd())
	cmd.AddCommand(newModelsDeleteCmd())

	return cmd
}

func newModelsListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List all model providers",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get("/model-providers")
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var providers []map[string]interface{}
			if err := json.Unmarshal(data, &providers); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			table := newTable("NAME", "PROVIDER", "MODELS", "STATUS")

			for _, p := range providers {
				name := stringField(p, "name")
				provider := stringField(p, "provider")
				models := formatModels(p["models"])
				status := stringField(p, "status")
				table.Append([]string{name, provider, models, status})
			}

			table.Render()
			return nil
		},
	}
}

func newModelsGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <name>",
		Short: "Get details of a model provider",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get(fmt.Sprintf("/model-providers/%s", name))
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var provider map[string]interface{}
			if err := json.Unmarshal(data, &provider); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			fmt.Printf("Name:     %s\n", stringField(provider, "name"))
			fmt.Printf("Provider: %s\n", stringField(provider, "provider"))
			fmt.Printf("Models:   %s\n", formatModels(provider["models"]))
			fmt.Printf("Status:   %s\n", stringField(provider, "status"))
			fmt.Printf("Endpoint: %s\n", stringField(provider, "endpoint"))

			return nil
		},
	}
}

func newModelsSpendCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "spend",
		Short: "Show model spend, budgets, and budget warnings",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get("/model-spend")
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var resp map[string]interface{}
			if err := json.Unmarshal(data, &resp); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			summary, _ := resp["summary"].(map[string]interface{})
			fmt.Println("Model spend")
			fmt.Printf("Estimated spend: %s\n", formatUSD(floatField(summary, "total_estimated_spend_usd")))
			fmt.Printf("Configured budget: %s\n", formatUSD(floatField(summary, "total_budget_usd")))
			fmt.Printf("Remaining budget: %s\n", formatUSD(floatField(summary, "remaining_budget_usd")))
			fmt.Printf("Budgeted models: %d\n", intField(summary, "budgeted_model_count"))
			fmt.Printf("Near budget: %d\n", intField(summary, "near_budget_count"))
			fmt.Printf("Budget reached: %d\n", intField(summary, "blocked_count"))
			if uncapped := floatField(summary, "uncapped_spend_usd"); uncapped > 0 {
				fmt.Printf("Uncapped spend: %s\n", formatUSD(uncapped))
			}

			if rows, ok := resp["warnings"].([]interface{}); ok && len(rows) > 0 {
				fmt.Println()
				fmt.Println("Warnings")
				renderModelSpendRows(rows)
			}
			if rows, ok := resp["top_models"].([]interface{}); ok && len(rows) > 0 {
				fmt.Println()
				fmt.Println("Top models")
				renderModelSpendRows(rows)
			}

			return nil
		},
	}
}

func newModelsCreateCmd() *cobra.Command {
	var filePath string

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a model provider from a JSON file",
		RunE: func(cmd *cobra.Command, args []string) error {
			fileData, err := os.ReadFile(filePath)
			if err != nil {
				return fmt.Errorf("failed to read file %q: %w", filePath, err)
			}

			var payload interface{}
			if err := json.Unmarshal(fileData, &payload); err != nil {
				return fmt.Errorf("invalid JSON in %q: %w", filePath, err)
			}

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Post("/model-providers", payload)
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			fmt.Println("Model provider created successfully.")
			return nil
		},
	}

	cmd.Flags().StringVar(&filePath, "file", "", "Path to JSON file with model provider definition")
	_ = cmd.MarkFlagRequired("file")

	return cmd
}

func newModelsDeleteCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "delete <name>",
		Short: "Delete a model provider",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			if err := c.Delete(fmt.Sprintf("/model-providers/%s", name)); err != nil {
				return err
			}

			fmt.Printf("Model provider %q deleted.\n", name)
			return nil
		},
	}
}

func renderModelSpendRows(rows []interface{}) {
	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"AGENT", "LABEL", "MODEL", "SPEND", "BUDGET", "REMAINING", "STATUS"})
	table.SetBorder(false)
	table.SetAutoWrapText(false)

	for _, row := range rows {
		item, _ := row.(map[string]interface{})
		table.Append([]string{
			firstNonEmpty(stringField(item, "agent_name"), stringField(item, "agent")),
			stringField(item, "label"),
			stringField(item, "model"),
			formatUSD(floatField(item, "estimated_spend_usd")),
			formatOptionalUSD(item["monthly_budget_usd"]),
			formatOptionalUSD(item["remaining_budget_usd"]),
			stringField(item, "status"),
		})
	}

	table.Render()
}

// formatModels converts the models field into a comma-separated string.
func formatModels(v interface{}) string {
	if v == nil {
		return ""
	}
	switch models := v.(type) {
	case []interface{}:
		var names []string
		for _, m := range models {
			names = append(names, fmt.Sprintf("%v", m))
		}
		return strings.Join(names, ", ")
	case string:
		return models
	default:
		return fmt.Sprintf("%v", v)
	}
}

func floatField(m map[string]interface{}, key string) float64 {
	if m == nil {
		return 0
	}
	switch v := m[key].(type) {
	case float64:
		return v
	case float32:
		return float64(v)
	case int:
		return float64(v)
	case int64:
		return float64(v)
	case json.Number:
		f, _ := v.Float64()
		return f
	default:
		return 0
	}
}

func intField(m map[string]interface{}, key string) int {
	if m == nil {
		return 0
	}
	switch v := m[key].(type) {
	case float64:
		return int(v)
	case int:
		return v
	case int64:
		return int(v)
	case json.Number:
		i, _ := v.Int64()
		return int(i)
	default:
		return 0
	}
}

func formatUSD(value float64) string {
	return fmt.Sprintf("$%.2f", value)
}

func formatOptionalUSD(value interface{}) string {
	switch v := value.(type) {
	case nil:
		return "uncapped"
	case float64:
		return formatUSD(v)
	case float32:
		return formatUSD(float64(v))
	case int:
		return formatUSD(float64(v))
	case int64:
		return formatUSD(float64(v))
	case json.Number:
		f, err := v.Float64()
		if err != nil {
			return fmt.Sprintf("%v", value)
		}
		return formatUSD(f)
	default:
		if fmt.Sprintf("%v", value) == "" {
			return "uncapped"
		}
		return fmt.Sprintf("%v", value)
	}
}
