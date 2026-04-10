package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
)

type deployOptions struct {
	Name             string
	Files            []string
	Tools            []string
	ModelFlag        string
	Policies         []string
	IdentityProvider string
	RequirementsFile string
	EntryPoint       string
	Framework        string
	DraftID          string
	ArtifactID       string
}

func newDeployCmd() *cobra.Command {
	var opts deployOptions

	cmd := &cobra.Command{
		Use:   "deploy",
		Short: "Deploy an agent",
		Long: `Deploy an agent from source files, a deploy draft, or an existing artifact.

Examples:
  runagents deploy --name my-agent --file agent.py --tool echo-tool --model openai/gpt-4o-mini
  runagents deploy --name billing-agent --draft-id draft_billing_v2 --policy billing-write-approval
  runagents deploy --name support-agent --artifact-id art_support_v3 --identity-provider google-oidc`,
		RunE: func(cmd *cobra.Command, args []string) error {
			cwd, err := os.Getwd()
			if err != nil {
				return fmt.Errorf("failed to determine current directory: %w", err)
			}

			payload, err := buildDeployPayload(opts, cwd)
			if err != nil {
				return err
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

			fmt.Printf("Agent %q deployed successfully.\n", strings.TrimSpace(opts.Name))
			if agent, ok := result["agent"]; ok {
				fmt.Printf("Agent: %v\n", agent)
			}
			if buildID, ok := result["build_id"]; ok && buildID != "" {
				fmt.Printf("Build ID: %v\n", buildID)
			}
			if createdTools, ok := result["tools_created"]; ok {
				fmt.Printf("Tools created: %v\n", createdTools)
			}

			return nil
		},
	}

	cmd.Flags().StringVar(&opts.Name, "name", "", "Agent name (required)")
	cmd.Flags().StringArrayVar(&opts.Files, "file", nil, "Source file(s) to deploy (repeatable)")
	cmd.Flags().StringArrayVar(&opts.Tools, "tool", nil, "Required tool name(s) (repeatable)")
	cmd.Flags().StringVar(&opts.ModelFlag, "model", "", "Model in provider/model format (for example openai/gpt-4o-mini)")
	cmd.Flags().StringArrayVar(&opts.Policies, "policy", nil, "Attach policies during deploy (repeatable)")
	cmd.Flags().StringVar(&opts.IdentityProvider, "identity-provider", "", "Bind an identity provider during deploy")
	cmd.Flags().StringVar(&opts.RequirementsFile, "requirements-file", "", "Path to a requirements file to include with source deploys")
	cmd.Flags().StringVar(&opts.EntryPoint, "entry-point", "", "Entrypoint file or module for source deploys")
	cmd.Flags().StringVar(&opts.Framework, "framework", "", "Framework hint for source deploys (for example langgraph)")
	cmd.Flags().StringVar(&opts.DraftID, "draft-id", "", "Deploy from an existing deploy draft")
	cmd.Flags().StringVar(&opts.ArtifactID, "artifact-id", "", "Deploy from an existing workflow artifact")
	_ = cmd.MarkFlagRequired("name")

	return cmd
}

func buildDeployPayload(opts deployOptions, cwd string) (map[string]any, error) {
	agentName := strings.TrimSpace(opts.Name)
	if agentName == "" {
		return nil, fmt.Errorf("--name is required")
	}

	mode, err := resolveDeploySourceMode(opts)
	if err != nil {
		return nil, err
	}

	payload := map[string]any{
		"agent_name": agentName,
	}

	switch mode {
	case "files":
		sourceFiles, err := readSourceFiles(opts.Files, cwd)
		if err != nil {
			return nil, err
		}
		payload["source_files"] = sourceFiles

		if strings.TrimSpace(opts.RequirementsFile) != "" {
			requirements, err := os.ReadFile(strings.TrimSpace(opts.RequirementsFile))
			if err != nil {
				return nil, fmt.Errorf("read requirements file: %w", err)
			}
			payload["requirements"] = string(requirements)
		}
		if strings.TrimSpace(opts.EntryPoint) != "" {
			payload["entry_point"] = strings.TrimSpace(opts.EntryPoint)
		}
		if strings.TrimSpace(opts.Framework) != "" {
			payload["framework"] = strings.TrimSpace(opts.Framework)
		}
	case "draft":
		payload["draft_id"] = strings.TrimSpace(opts.DraftID)
	case "artifact":
		payload["artifact_id"] = strings.TrimSpace(opts.ArtifactID)
	default:
		return nil, fmt.Errorf("unsupported deploy source mode %q", mode)
	}

	if len(opts.Tools) > 0 {
		payload["required_tools"] = normalizedNonEmptyStrings(opts.Tools)
	}
	if len(opts.Policies) > 0 {
		payload["policies"] = normalizedNonEmptyStrings(opts.Policies)
	}
	if strings.TrimSpace(opts.IdentityProvider) != "" {
		payload["identity_provider"] = strings.TrimSpace(opts.IdentityProvider)
	}
	if strings.TrimSpace(opts.ModelFlag) != "" {
		llmConfigs, err := parseDeployModelFlag(opts.ModelFlag)
		if err != nil {
			return nil, err
		}
		payload["llm_configs"] = llmConfigs
	}

	return payload, nil
}

func resolveDeploySourceMode(opts deployOptions) (string, error) {
	sourceModes := 0
	if len(opts.Files) > 0 {
		sourceModes++
	}
	if strings.TrimSpace(opts.DraftID) != "" {
		sourceModes++
	}
	if strings.TrimSpace(opts.ArtifactID) != "" {
		sourceModes++
	}
	if sourceModes == 0 {
		return "", fmt.Errorf("provide exactly one deploy source: --file, --draft-id, or --artifact-id")
	}
	if sourceModes > 1 {
		return "", fmt.Errorf("provide only one deploy source: --file, --draft-id, or --artifact-id")
	}

	if len(opts.Files) == 0 {
		if strings.TrimSpace(opts.RequirementsFile) != "" {
			return "", fmt.Errorf("--requirements-file can only be used with --file")
		}
		if strings.TrimSpace(opts.EntryPoint) != "" {
			return "", fmt.Errorf("--entry-point can only be used with --file")
		}
		if strings.TrimSpace(opts.Framework) != "" {
			return "", fmt.Errorf("--framework can only be used with --file")
		}
	}

	if len(opts.Files) > 0 {
		return "files", nil
	}
	if strings.TrimSpace(opts.DraftID) != "" {
		return "draft", nil
	}
	return "artifact", nil
}

func parseDeployModelFlag(modelFlag string) ([]map[string]string, error) {
	parts := strings.SplitN(strings.TrimSpace(modelFlag), "/", 2)
	if len(parts) != 2 || strings.TrimSpace(parts[0]) == "" || strings.TrimSpace(parts[1]) == "" {
		return nil, fmt.Errorf("--model must be in provider/model format (for example openai/gpt-4o-mini)")
	}
	return []map[string]string{{
		"provider": strings.TrimSpace(parts[0]),
		"model":    strings.TrimSpace(parts[1]),
	}}, nil
}

func normalizedNonEmptyStrings(values []string) []string {
	out := make([]string, 0, len(values))
	for _, value := range values {
		if trimmed := strings.TrimSpace(value); trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return out
}
