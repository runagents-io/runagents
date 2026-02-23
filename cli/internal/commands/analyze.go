package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

func newAnalyzeCmd() *cobra.Command {
	var files []string

	cmd := &cobra.Command{
		Use:   "analyze",
		Short: "Analyze source files for tools, models, and secrets",
		Long: `Analyze source files using the RunAgents ingestion service.
Detects tools, model usages, secrets, outbound destinations, and requirements.

Example:
  runagents analyze --file agent.py`,
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(files) == 0 {
				return fmt.Errorf("at least one --file is required")
			}

			// Read source files into a map.
			sourceFiles := make(map[string]string)
			for _, f := range files {
				data, err := os.ReadFile(f)
				if err != nil {
					return fmt.Errorf("failed to read file %q: %w", f, err)
				}
				filename := filepath.Base(f)
				sourceFiles[filename] = string(data)
			}

			payload := map[string]interface{}{
				"files": sourceFiles,
			}

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Post("/ingestion/analyze", payload)
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var result map[string]interface{}
			if err := json.Unmarshal(data, &result); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			// Display detected tools.
			if tools, ok := result["tools"]; ok {
				printSection("Detected Tools", tools)
			}

			// Display model usages.
			if models, ok := result["model_usages"]; ok {
				printModelUsages(models)
			}

			// Display secrets.
			if secrets, ok := result["secrets"]; ok {
				printSecrets(secrets)
			}

			// Display requirements.
			if reqs, ok := result["detected_requirements"]; ok {
				printSection("Detected Requirements", reqs)
			}

			// Display outbound destinations.
			if destinations, ok := result["outbound_destinations"]; ok {
				printSection("Outbound Destinations", destinations)
			}

			// Display entry point.
			if entryPoint, ok := result["entry_point"]; ok {
				fmt.Printf("\nEntry Point: %v\n", entryPoint)
			}

			return nil
		},
	}

	cmd.Flags().StringArrayVar(&files, "file", nil, "Source file(s) to analyze (can be specified multiple times)")

	return cmd
}

func printSection(title string, data interface{}) {
	fmt.Printf("\n%s:\n", title)
	items, ok := data.([]interface{})
	if !ok || len(items) == 0 {
		fmt.Println("  (none)")
		return
	}
	for _, item := range items {
		fmt.Printf("  - %v\n", item)
	}
}

func printModelUsages(data interface{}) {
	fmt.Println("\nModel Usages:")
	items, ok := data.([]interface{})
	if !ok || len(items) == 0 {
		fmt.Println("  (none)")
		return
	}

	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"ROLE", "MODEL", "FILE", "LINE"})
	table.SetBorder(false)
	table.SetAutoWrapText(false)

	for _, item := range items {
		m, ok := item.(map[string]interface{})
		if !ok {
			continue
		}
		role := stringField(m, "role")
		model := stringField(m, "variable_name")
		file := stringField(m, "file")
		line := stringField(m, "line")
		table.Append([]string{role, model, file, line})
	}

	table.Render()
}

func printSecrets(data interface{}) {
	fmt.Println("\nSecrets Detected:")
	items, ok := data.([]interface{})
	if !ok || len(items) == 0 {
		fmt.Println("  (none)")
		return
	}

	var descriptions []string
	for _, item := range items {
		m, ok := item.(map[string]interface{})
		if !ok {
			descriptions = append(descriptions, fmt.Sprintf("  - %v", item))
			continue
		}
		file := stringField(m, "file")
		line := stringField(m, "line")
		desc := stringField(m, "description")
		descriptions = append(descriptions, fmt.Sprintf("  - %s:%s %s", file, line, desc))
	}
	fmt.Println(strings.Join(descriptions, "\n"))
}
