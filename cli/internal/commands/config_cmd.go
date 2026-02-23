package commands

import (
	"fmt"
	"strings"

	"github.com/runagents/runagents/cli/internal/config"
	"github.com/spf13/cobra"
)

func newConfigCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "Manage CLI configuration",
	}

	cmd.AddCommand(newConfigSetCmd())
	cmd.AddCommand(newConfigGetCmd())

	return cmd
}

func newConfigSetCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "set <key> <value>",
		Short: "Set a configuration value",
		Long:  "Set a configuration value. Valid keys: endpoint, api-key.",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			key := args[0]
			value := args[1]

			cfg, err := config.Load()
			if err != nil {
				return err
			}

			switch key {
			case "endpoint":
				cfg.Endpoint = value
			case "api-key":
				cfg.APIKey = value
			default:
				return fmt.Errorf("unknown config key %q; valid keys: endpoint, api-key", key)
			}

			if err := config.Save(cfg); err != nil {
				return err
			}

			fmt.Printf("Config %q set successfully.\n", key)
			return nil
		},
	}
	return cmd
}

func newConfigGetCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get",
		Short: "Show current configuration",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cfg, err := config.Load()
			if err != nil {
				return err
			}

			fmt.Printf("Endpoint: %s\n", cfg.Endpoint)
			if cfg.APIKey != "" {
				masked := maskAPIKey(cfg.APIKey)
				fmt.Printf("API Key:  %s\n", masked)
			} else {
				fmt.Println("API Key:  (not set)")
			}
			return nil
		},
	}
	return cmd
}

// maskAPIKey masks all but the first 4 and last 4 characters of a key.
func maskAPIKey(key string) string {
	if len(key) <= 8 {
		return strings.Repeat("*", len(key))
	}
	return key[:4] + strings.Repeat("*", len(key)-8) + key[len(key)-4:]
}
