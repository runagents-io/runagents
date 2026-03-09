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
	flagEndpoint  string
	flagAPIKey    string
	flagNamespace string
	flagOutput    string
)

var rootCmd = &cobra.Command{
	Use:          "runagents",
	Short:        "RunAgents CLI -- manage AI agents, tools, and runs",
	Long:         "RunAgents CLI -- manage AI agents, tools, and runs from the terminal.\nInteracts with the RunAgents platform API to deploy agents, register tools,\nmanage model providers, monitor runs, and handle approvals.",
	SilenceUsage: true,
	RunE: func(cmd *cobra.Command, args []string) error {
		mode, err := resolvedAssistantMode()
		if err != nil {
			return err
		}
		if !isInteractiveTerminal() {
			return cmd.Help()
		}
		if mode != config.AssistantModeRunAgents {
			fmt.Fprintf(os.Stderr, "Assistant mode is %q; interactive copilot shell is disabled.\n", mode)
			fmt.Fprintln(os.Stderr, "Use explicit CLI commands, or set 'runagents config set assistant-mode runagents' to enable the shell.")
			return cmd.Help()
		}
		return runDefaultInteractiveShell()
	},
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
	rootCmd.PersistentFlags().StringVar(&flagNamespace, "namespace", "", "Workspace namespace (overrides config)")
	rootCmd.PersistentFlags().StringVarP(&flagOutput, "output", "o", "table", "Output format: table or json")

	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(newConfigCmd())
	rootCmd.AddCommand(newContextCmd())
	rootCmd.AddCommand(newActionCmd())
	rootCmd.AddCommand(newAgentsCmd())
	rootCmd.AddCommand(newToolsCmd())
	rootCmd.AddCommand(newModelsCmd())
	rootCmd.AddCommand(newRunsCmd())
	rootCmd.AddCommand(newDeployCmd())
	rootCmd.AddCommand(newApprovalsCmd())
	rootCmd.AddCommand(newStarterKitCmd())
	rootCmd.AddCommand(newAnalyzeCmd())
	rootCmd.AddCommand(newCopilotCmd())
}

// Execute runs the root command.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}

// newAPIClient creates a new API client using config and flag overrides.
func newAPIClient() (*client.Client, error) {
	endpoint, apiKey, namespace, err := resolvedAPISettings()
	if err != nil {
		return nil, err
	}
	if endpoint == "" {
		return nil, fmt.Errorf("no endpoint configured; run 'runagents config set endpoint <url>' or use --endpoint")
	}
	if namespace == "" {
		return nil, fmt.Errorf("no namespace configured; run 'runagents config set namespace <name>' or use --namespace")
	}

	return client.NewClient(endpoint, apiKey, namespace), nil
}

func resolvedAPISettings() (endpoint, apiKey, namespace string, err error) {
	cfg, err := config.Load()
	if err != nil {
		return "", "", "", fmt.Errorf("failed to load config: %w", err)
	}

	endpoint = cfg.Endpoint
	if flagEndpoint != "" {
		endpoint = flagEndpoint
	}

	apiKey = cfg.APIKey
	if flagAPIKey != "" {
		apiKey = flagAPIKey
	}
	namespace = cfg.Namespace
	if flagNamespace != "" {
		namespace = flagNamespace
	}
	return endpoint, apiKey, namespace, nil
}

func resolvedAssistantMode() (string, error) {
	cfg, err := config.Load()
	if err != nil {
		return "", fmt.Errorf("failed to load config: %w", err)
	}
	return cfg.AssistantMode, nil
}

// isJSONOutput returns true if the user requested JSON output.
func isJSONOutput() bool {
	return flagOutput == "json"
}

func isInteractiveTerminal() bool {
	in, err := os.Stdin.Stat()
	if err != nil {
		return false
	}
	out, err := os.Stdout.Stat()
	if err != nil {
		return false
	}
	return (in.Mode()&os.ModeCharDevice) != 0 && (out.Mode()&os.ModeCharDevice) != 0
}
