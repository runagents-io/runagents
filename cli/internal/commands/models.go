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

			data, err := c.Get("/api/model-providers")
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

			table := tablewriter.NewWriter(os.Stdout)
			table.SetHeader([]string{"NAME", "PROVIDER", "MODELS", "STATUS"})
			table.SetBorder(false)
			table.SetAutoWrapText(false)

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

			data, err := c.Get(fmt.Sprintf("/api/model-providers/%s", name))
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

			data, err := c.Post("/api/model-providers", payload)
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

			if err := c.Delete(fmt.Sprintf("/api/model-providers/%s", name)); err != nil {
				return err
			}

			fmt.Printf("Model provider %q deleted.\n", name)
			return nil
		},
	}
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
