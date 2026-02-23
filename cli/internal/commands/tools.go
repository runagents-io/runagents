package commands

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

func newToolsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "tools",
		Short: "Manage tools",
	}

	cmd.AddCommand(newToolsListCmd())
	cmd.AddCommand(newToolsGetCmd())
	cmd.AddCommand(newToolsCreateCmd())
	cmd.AddCommand(newToolsDeleteCmd())

	return cmd
}

func newToolsListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List all tools",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get("/api/tools")
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var tools []map[string]interface{}
			if err := json.Unmarshal(data, &tools); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			table := tablewriter.NewWriter(os.Stdout)
			table.SetHeader([]string{"NAME", "TOPOLOGY", "BASE_URL", "ACCESS", "STATUS"})
			table.SetBorder(false)
			table.SetAutoWrapText(false)

			for _, t := range tools {
				name := stringField(t, "name")
				topology := stringField(t, "topology")
				baseURL := stringField(t, "base_url")
				access := stringField(t, "access_mode")
				status := stringField(t, "status")
				table.Append([]string{name, topology, baseURL, access, status})
			}

			table.Render()
			return nil
		},
	}
}

func newToolsGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <name>",
		Short: "Get details of a tool",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get(fmt.Sprintf("/api/tools/%s", name))
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var tool map[string]interface{}
			if err := json.Unmarshal(data, &tool); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			fmt.Printf("Name:     %s\n", stringField(tool, "name"))
			fmt.Printf("Topology: %s\n", stringField(tool, "topology"))
			fmt.Printf("Base URL: %s\n", stringField(tool, "base_url"))
			fmt.Printf("Access:   %s\n", stringField(tool, "access_mode"))
			fmt.Printf("Status:   %s\n", stringField(tool, "status"))

			if auth, ok := tool["auth"]; ok {
				fmt.Printf("Auth:     %v\n", auth)
			}

			return nil
		},
	}
}

func newToolsCreateCmd() *cobra.Command {
	var filePath string

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a tool from a JSON file",
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

			data, err := c.Post("/api/tools", payload)
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			fmt.Println("Tool created successfully.")
			return nil
		},
	}

	cmd.Flags().StringVar(&filePath, "file", "", "Path to JSON file with tool definition")
	_ = cmd.MarkFlagRequired("file")

	return cmd
}

func newToolsDeleteCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "delete <name>",
		Short: "Delete a tool",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			if err := c.Delete(fmt.Sprintf("/api/tools/%s", name)); err != nil {
				return err
			}

			fmt.Printf("Tool %q deleted.\n", name)
			return nil
		},
	}
}
