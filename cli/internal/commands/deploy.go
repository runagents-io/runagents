package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
)

func newDeployCmd() *cobra.Command {
	var (
		name      string
		files     []string
		tools     []string
		modelFlag string
	)

	cmd := &cobra.Command{
		Use:   "deploy",
		Short: "Deploy an agent",
		Long: `Deploy an agent by uploading source files and specifying tools and model.

Example:
  runagents deploy --name my-agent --file agent.py --tool echo-tool --model openai/gpt-4o-mini`,
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

			// Build the deploy payload.
			payload := map[string]interface{}{
				"name":         name,
				"source_files": sourceFiles,
			}

			if len(tools) > 0 {
				payload["required_tools"] = tools
			}

			// Parse --model flag: provider/model format.
			if modelFlag != "" {
				parts := strings.SplitN(modelFlag, "/", 2)
				if len(parts) != 2 {
					return fmt.Errorf("--model must be in provider/model format (e.g., openai/gpt-4o-mini)")
				}
				payload["llm_configs"] = []map[string]string{
					{
						"provider": parts[0],
						"model":    parts[1],
					},
				}
			}

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Post("/api/deploy", payload)
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var result map[string]interface{}
			if err := json.Unmarshal(data, &result); err != nil {
				fmt.Println("Deploy request submitted.")
				return nil
			}

			fmt.Printf("Agent %q deployed successfully.\n", name)
			if agent, ok := result["agent"]; ok {
				fmt.Printf("Agent: %v\n", agent)
			}
			if createdTools, ok := result["tools_created"]; ok {
				fmt.Printf("Tools created: %v\n", createdTools)
			}

			return nil
		},
	}

	cmd.Flags().StringVar(&name, "name", "", "Agent name (required)")
	cmd.Flags().StringArrayVar(&files, "file", nil, "Source file(s) to deploy (can be specified multiple times)")
	cmd.Flags().StringArrayVar(&tools, "tool", nil, "Required tool name(s) (can be specified multiple times)")
	cmd.Flags().StringVar(&modelFlag, "model", "", "Model in provider/model format (e.g., openai/gpt-4o-mini)")
	_ = cmd.MarkFlagRequired("name")

	return cmd
}
