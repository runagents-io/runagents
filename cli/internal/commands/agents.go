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

			data, err := c.Get("/api/agents")
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

			table := tablewriter.NewWriter(os.Stdout)
			table.SetHeader([]string{"NAME", "STATUS", "IMAGE"})
			table.SetBorder(false)
			table.SetAutoWrapText(false)

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
		Use:   "get <namespace> <name>",
		Short: "Get details of an agent",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			ns := args[0]
			name := args[1]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get(fmt.Sprintf("/api/agents/%s/%s", ns, name))
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

func newAgentsDeleteCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "delete <namespace> <name>",
		Short: "Delete an agent",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			ns := args[0]
			name := args[1]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			if err := c.Delete(fmt.Sprintf("/api/agents/%s/%s", ns, name)); err != nil {
				return err
			}

			fmt.Printf("Agent %s/%s deleted.\n", ns, name)
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
