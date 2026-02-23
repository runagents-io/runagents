package commands

import (
	"fmt"
	"os"

	"github.com/runagents/runagents/cli/internal/client"
	"github.com/runagents/runagents/cli/internal/config"
	"github.com/spf13/cobra"
)

var (
	// Version is set at build time via ldflags.
	Version = "dev"

	// Persistent flag values.
	flagEndpoint string
	flagAPIKey   string
	flagOutput   string
)

var rootCmd = &cobra.Command{
	Use:   "runagents",
	Short: "RunAgents CLI -- manage AI agents, tools, and runs",
	Long:  "RunAgents CLI -- manage AI agents, tools, and runs from the terminal.\nInteracts with the RunAgents platform API to deploy agents, register tools,\nmanage model providers, monitor runs, and handle approvals.",
	SilenceUsage: true,
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the CLI version",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("runagents version %s\n", Version)
	},
}

func init() {
	rootCmd.PersistentFlags().StringVar(&flagEndpoint, "endpoint", "", "API endpoint URL (overrides config)")
	rootCmd.PersistentFlags().StringVar(&flagAPIKey, "api-key", "", "API key (overrides config)")
	rootCmd.PersistentFlags().StringVarP(&flagOutput, "output", "o", "table", "Output format: table or json")

	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(newConfigCmd())
	rootCmd.AddCommand(newAgentsCmd())
	rootCmd.AddCommand(newToolsCmd())
	rootCmd.AddCommand(newModelsCmd())
	rootCmd.AddCommand(newRunsCmd())
	rootCmd.AddCommand(newDeployCmd())
	rootCmd.AddCommand(newApprovalsCmd())
	rootCmd.AddCommand(newStarterKitCmd())
	rootCmd.AddCommand(newAnalyzeCmd())
}

// Execute runs the root command.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}

// newAPIClient creates a new API client using config and flag overrides.
func newAPIClient() (*client.Client, error) {
	cfg, err := config.Load()
	if err != nil {
		return nil, fmt.Errorf("failed to load config: %w", err)
	}

	endpoint := cfg.Endpoint
	if flagEndpoint != "" {
		endpoint = flagEndpoint
	}

	apiKey := cfg.APIKey
	if flagAPIKey != "" {
		apiKey = flagAPIKey
	}

	if endpoint == "" {
		return nil, fmt.Errorf("no endpoint configured; run 'runagents config set endpoint <url>' or use --endpoint")
	}

	return client.NewClient(endpoint, apiKey), nil
}

// isJSONOutput returns true if the user requested JSON output.
func isJSONOutput() bool {
	return flagOutput == "json"
}
