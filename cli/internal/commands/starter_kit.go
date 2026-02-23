package commands

import (
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"
)

func newStarterKitCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "starter-kit",
		Short: "Seed the platform with starter resources (echo-tool, playground-llm)",
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Post("/api/starter-kit", nil)
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var result map[string]interface{}
			if err := json.Unmarshal(data, &result); err != nil {
				fmt.Println("Starter kit seeded successfully.")
				return nil
			}

			fmt.Println("Starter kit seeded successfully.")
			if toolsCreated, ok := result["tools_created"]; ok {
				fmt.Printf("Tools created:           %v\n", toolsCreated)
			}
			if modelsCreated, ok := result["model_providers_created"]; ok {
				fmt.Printf("Model providers created:  %v\n", modelsCreated)
			}
			if msg, ok := result["message"]; ok {
				fmt.Printf("Message: %v\n", msg)
			}

			return nil
		},
	}
}
