package commands

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

func newAgentsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "agents",
		Short: "Manage agents",
	}

	cmd.AddCommand(newAgentsListCmd())
	cmd.AddCommand(newAgentsGetCmd())
	cmd.AddCommand(newAgentsConfigCmd())
	cmd.AddCommand(newAgentsDeleteCmd())

	return cmd
}

func newAgentsListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List all agents",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get("/agents")
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var agents []map[string]interface{}
			if err := json.Unmarshal(data, &agents); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			table := newTable("NAME", "STATUS", "IMAGE")

			for _, a := range agents {
				name := stringField(a, "name")
				status := stringField(a, "status")
				image := stringField(a, "image")
				table.Append([]string{name, status, image})
			}

			table.Render()
			return nil
		},
	}
}

func newAgentsGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <name>",
		Short: "Get details of an agent",
		Args:  cobra.RangeArgs(1, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]
			if len(args) == 2 {
				name = args[1]
			}

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get(fmt.Sprintf("/agents/%s", name))
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var agent map[string]interface{}
			if err := json.Unmarshal(data, &agent); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			fmt.Printf("Name:      %s\n", stringField(agent, "name"))
			fmt.Printf("Namespace: %s\n", stringField(agent, "namespace"))
			fmt.Printf("Status:    %s\n", stringField(agent, "status"))
			fmt.Printf("Image:     %s\n", stringField(agent, "image"))

			if tools, ok := agent["required_tools"]; ok {
				fmt.Printf("Tools:     %v\n", tools)
			}
			if llm, ok := agent["llm_config"]; ok {
				fmt.Printf("LLM:       %v\n", llm)
			}

			return nil
		},
	}
}

func newAgentsConfigCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "Inspect and update agent configuration",
	}

	cmd.AddCommand(newAgentsConfigGetCmd())
	cmd.AddCommand(newAgentsConfigUpdateCmd())

	return cmd
}

func newAgentsConfigGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <name>",
		Short: "Get agent configuration, model budgets, and current model usage",
		Args:  cobra.RangeArgs(1, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]
			if len(args) == 2 {
				name = args[1]
			}

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get(fmt.Sprintf("/agents/%s/config", name))
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var cfg map[string]interface{}
			if err := json.Unmarshal(data, &cfg); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			fmt.Printf("Agent:     %s\n", stringField(cfg, "agent_name"))
			fmt.Printf("Namespace: %s\n", stringField(cfg, "namespace"))
			fmt.Printf("Image:     %s\n", stringField(cfg, "image"))
			if prompt := stringField(cfg, "system_prompt"); prompt != "" {
				fmt.Printf("Prompt:    %s\n", prompt)
			}
			if idp := stringField(cfg, "identity_provider"); idp != "" {
				fmt.Printf("Identity:  %s\n", idp)
			}

			if rows, ok := cfg["llm_configs"].([]interface{}); ok && len(rows) > 0 {
				fmt.Println()
				fmt.Println("Model configuration")
				table := tablewriter.NewWriter(os.Stdout)
				table.SetHeader([]string{"ROLE", "PROVIDER", "MODEL", "BUDGET"})
				table.SetBorder(false)
				table.SetAutoWrapText(false)
				for _, row := range rows {
					item, _ := row.(map[string]interface{})
					table.Append([]string{
						stringField(item, "role"),
						firstNonEmpty(stringField(item, "model_provider"), stringField(item, "provider")),
						stringField(item, "model"),
						formatOptionalUSD(item["monthly_budget_usd"]),
					})
				}
				table.Render()
			}

			if rows, ok := cfg["model_usage"].([]interface{}); ok && len(rows) > 0 {
				fmt.Println()
				fmt.Println("Current model usage")
				table := tablewriter.NewWriter(os.Stdout)
				table.SetHeader([]string{"LABEL", "MODEL", "SPEND", "BUDGET", "REMAINING", "STATUS"})
				table.SetBorder(false)
				table.SetAutoWrapText(false)
				for _, row := range rows {
					item, _ := row.(map[string]interface{})
					table.Append([]string{
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

			return nil
		},
	}
}

func newAgentsConfigUpdateCmd() *cobra.Command {
	var filePath string

	cmd := &cobra.Command{
		Use:   "update <name>",
		Short: "Update agent configuration from a JSON file",
		Args:  cobra.RangeArgs(1, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]
			if len(args) == 2 {
				name = args[1]
			}
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

			data, err := c.Put(fmt.Sprintf("/agents/%s/config", name), payload)
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			fmt.Printf("Agent %q configuration updated.\n", name)
			return nil
		},
	}

	cmd.Flags().StringVar(&filePath, "file", "", "Path to JSON file with agent configuration update")
	_ = cmd.MarkFlagRequired("file")

	return cmd
}

func newAgentsDeleteCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "delete <name>",
		Short: "Delete an agent",
		Args:  cobra.RangeArgs(1, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			ns := ""
			name := args[0]
			if len(args) == 2 {
				ns = args[0]
				name = args[1]
			}

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			if err := c.Delete(fmt.Sprintf("/agents/%s", name)); err != nil {
				return err
			}

			if ns != "" {
				fmt.Printf("Agent %s/%s deleted.\n", ns, name)
			} else {
				fmt.Printf("Agent %s deleted.\n", name)
			}
			return nil
		},
	}
}

// stringField safely extracts a string field from a map.
func stringField(m map[string]interface{}, key string) string {
	v, ok := m[key]
	if !ok {
		return ""
	}
	s, ok := v.(string)
	if !ok {
		return fmt.Sprintf("%v", v)
	}
	return s
}
