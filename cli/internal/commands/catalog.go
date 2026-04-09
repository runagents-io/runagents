package commands

import (
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/spf13/cobra"
)

const catalogManifestFilename = "runagents.catalog.json"

type catalogListResponse struct {
	GeneratedAt string             `json:"generated_at,omitempty"`
	Items       []catalogIndexItem `json:"items"`
	Total       int                `json:"total"`
	Page        int                `json:"page"`
	PageSize    int                `json:"page_size"`
}

type catalogIndexItem struct {
	ID                   string                 `json:"id"`
	Name                 string                 `json:"name"`
	Summary              string                 `json:"summary,omitempty"`
	Description          string                 `json:"description,omitempty"`
	Category             string                 `json:"category,omitempty"`
	Tags                 []string               `json:"tags,omitempty"`
	LatestVersion        string                 `json:"latest_version"`
	RequiredIntegrations []string               `json:"required_integrations,omitempty"`
	DefaultPolicies      []string               `json:"default_policies,omitempty"`
	GovernanceTraits     []string               `json:"governance_traits,omitempty"`
	Complexity           string                 `json:"complexity,omitempty"`
	Metadata             map[string]interface{} `json:"metadata,omitempty"`
}

type catalogPrompt struct {
	Title   string `json:"title,omitempty"`
	Content string `json:"content,omitempty"`
}

type catalogDeploymentTemplate struct {
	WorkflowRef      string                 `json:"workflowRef,omitempty"`
	ArtifactID       string                 `json:"artifactId,omitempty"`
	SourceType       string                 `json:"sourceType,omitempty"`
	SourceFiles      map[string]string      `json:"sourceFiles,omitempty"`
	WorkflowJSON     map[string]interface{} `json:"workflowJson,omitempty"`
	AgentName        string                 `json:"agentName,omitempty"`
	SystemPrompt     string                 `json:"systemPrompt,omitempty"`
	RequiredTools    []string               `json:"requiredTools,omitempty"`
	RecommendedTools []string               `json:"recommendedTools,omitempty"`
	Policies         []string               `json:"policies,omitempty"`
	AccessMode       string                 `json:"accessMode,omitempty"`
	IdentityProvider string                 `json:"identityProvider,omitempty"`
}

type catalogManifest struct {
	ID                    string                    `json:"id"`
	Version               string                    `json:"version"`
	Name                  string                    `json:"name"`
	Summary               string                    `json:"summary,omitempty"`
	Description           string                    `json:"description,omitempty"`
	Category              string                    `json:"category,omitempty"`
	Tags                  []string                  `json:"tags,omitempty"`
	DefaultModel          string                    `json:"defaultModel,omitempty"`
	RequiredIntegrations  []string                  `json:"requiredIntegrations,omitempty"`
	DefaultPolicies       []string                  `json:"defaultPolicies,omitempty"`
	GovernanceTraits      []string                  `json:"governanceTraits,omitempty"`
	AccessRecommendations []string                  `json:"accessRecommendations,omitempty"`
	UseCases              []string                  `json:"useCases,omitempty"`
	Prompts               []catalogPrompt           `json:"prompts,omitempty"`
	DeploymentTemplate    catalogDeploymentTemplate `json:"deploymentTemplate"`
	Metadata              map[string]interface{}    `json:"metadata,omitempty"`
	Changelog             string                    `json:"changelog,omitempty"`
	PublishedAt           string                    `json:"publishedAt,omitempty"`
}

type catalogVersionsResponse struct {
	AgentID  string                  `json:"agent_id"`
	Versions []catalogVersionSummary `json:"versions"`
}

type catalogVersionSummary struct {
	Version     string `json:"version"`
	PublishedAt string `json:"published_at,omitempty"`
	Summary     string `json:"summary,omitempty"`
	Changelog   string `json:"changelog,omitempty"`
}

func newCatalogCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "catalog",
		Short: "Discover and deploy agents from the RunAgents catalog",
	}

	cmd.AddCommand(newCatalogListCmd())
	cmd.AddCommand(newCatalogShowCmd())
	cmd.AddCommand(newCatalogVersionsCmd())
	cmd.AddCommand(newCatalogInitCmd())
	cmd.AddCommand(newCatalogDeployCmd())

	return cmd
}

func newCatalogListCmd() *cobra.Command {
	var (
		search       string
		categories   []string
		tags         []string
		integrations []string
		governance   []string
		page         int
		pageSize     int
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List catalog agents",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			query := catalogListQuery(search, categories, tags, integrations, governance, page, pageSize)

			data, err := c.GetWithQuery("/api/catalog", query)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var resp catalogListResponse
			if err := json.Unmarshal(data, &resp); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			if len(resp.Items) == 0 {
				fmt.Println("No catalog agents found.")
				return nil
			}

			table := newTable("ID", "NAME", "CATEGORY", "LATEST", "INTEGRATIONS")
			for _, item := range resp.Items {
				table.Append([]string{
					item.ID,
					item.Name,
					item.Category,
					item.LatestVersion,
					strings.Join(item.RequiredIntegrations, ", "),
				})
			}
			table.Render()
			return nil
		},
	}

	cmd.Flags().StringVar(&search, "search", "", "Search catalog entries by name, summary, tag, or integration")
	cmd.Flags().StringSliceVar(&categories, "category", nil, "Filter by category (repeatable)")
	cmd.Flags().StringSliceVar(&tags, "tag", nil, "Filter by tag (repeatable)")
	cmd.Flags().StringSliceVar(&integrations, "integration", nil, "Filter by required integration (repeatable)")
	cmd.Flags().StringSliceVar(&governance, "governance", nil, "Filter by governance trait (repeatable)")
	cmd.Flags().IntVar(&page, "page", 1, "Page number")
	cmd.Flags().IntVar(&pageSize, "page-size", 24, "Items per page")
	return cmd
}

func newCatalogShowCmd() *cobra.Command {
	var version string
	cmd := &cobra.Command{
		Use:   "show <id>",
		Short: "Show details for a catalog agent",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			manifest, err := fetchCatalogManifest(args[0], version)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				data, err := json.MarshalIndent(manifest, "", "  ")
				if err != nil {
					return fmt.Errorf("marshal manifest: %w", err)
				}
				fmt.Println(string(data))
				return nil
			}
			printCatalogManifest(manifest)
			return nil
		},
	}
	cmd.Flags().StringVar(&version, "version", "", "Specific catalog version to show")
	return cmd
}

func newCatalogVersionsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "versions <id>",
		Short: "List published versions for a catalog agent",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get(fmt.Sprintf("/api/catalog/%s/versions", args[0]))
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var resp catalogVersionsResponse
			if err := json.Unmarshal(data, &resp); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			if len(resp.Versions) == 0 {
				fmt.Printf("No versions found for %s.\n", args[0])
				return nil
			}
			table := newTable("VERSION", "PUBLISHED", "SUMMARY")
			for _, version := range resp.Versions {
				table.Append([]string{version.Version, version.PublishedAt, version.Summary})
			}
			table.Render()
			return nil
		},
	}
	return cmd
}

func newCatalogInitCmd() *cobra.Command {
	var (
		version string
		force   bool
	)
	cmd := &cobra.Command{
		Use:   "init <id> [dir]",
		Short: "Initialize a local working copy from a catalog agent",
		Args:  cobra.RangeArgs(1, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			manifest, err := fetchCatalogManifest(args[0], version)
			if err != nil {
				return err
			}
			targetDir := args[0]
			if len(args) == 2 {
				targetDir = args[1]
			}
			summary, err := writeCatalogTemplate(targetDir, manifest, force)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				data, err := json.MarshalIndent(summary, "", "  ")
				if err != nil {
					return fmt.Errorf("marshal init summary: %w", err)
				}
				fmt.Println(string(data))
				return nil
			}
			fmt.Printf("Initialized %s in %s\n", manifest.Name, summary.TargetDir)
			fmt.Printf("Wrote %d source files and %s\n", len(summary.SourceFiles), catalogManifestFilename)
			return nil
		},
	}
	cmd.Flags().StringVar(&version, "version", "", "Specific catalog version to initialize")
	cmd.Flags().BoolVar(&force, "force", false, "Overwrite existing files in the target directory")
	return cmd
}

func newCatalogDeployCmd() *cobra.Command {
	var (
		version          string
		name             string
		tools            []string
		modelFlag        string
		policies         []string
		identityProvider string
		dryRun           bool
	)
	cmd := &cobra.Command{
		Use:   "deploy <id>",
		Short: "Deploy a catalog agent directly from its manifest",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			manifest, err := fetchCatalogManifest(args[0], version)
			if err != nil {
				return err
			}
			payload, err := buildCatalogDeployPayload(manifest, catalogDeployOptions{
				Name:             name,
				Tools:            tools,
				Model:            modelFlag,
				Policies:         policies,
				IdentityProvider: identityProvider,
			})
			if err != nil {
				return err
			}

			if dryRun {
				data, err := json.MarshalIndent(payload, "", "  ")
				if err != nil {
					return fmt.Errorf("marshal deploy payload: %w", err)
				}
				fmt.Println(string(data))
				return nil
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

			var result map[string]any
			if err := json.Unmarshal(data, &result); err != nil {
				fmt.Printf("Catalog deploy submitted for %q.\n", payload["agent_name"])
				return nil
			}
			fmt.Printf("Catalog agent %q deployed successfully.\n", payload["agent_name"])
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
	cmd.Flags().StringVar(&version, "version", "", "Specific catalog version to deploy")
	cmd.Flags().StringVar(&name, "name", "", "Override the deployed agent name")
	cmd.Flags().StringArrayVar(&tools, "tool", nil, "Override required tool names (repeatable)")
	cmd.Flags().StringVar(&modelFlag, "model", "", "Override the model as provider/model")
	cmd.Flags().StringArrayVar(&policies, "policy", nil, "Attach policies during deploy (repeatable)")
	cmd.Flags().StringVar(&identityProvider, "identity-provider", "", "Override the deploy identity provider")
	cmd.Flags().BoolVar(&dryRun, "dry-run", false, "Print the deploy payload instead of calling the API")
	return cmd
}

type catalogInitSummary struct {
	TargetDir   string   `json:"target_dir"`
	Manifest    string   `json:"manifest"`
	SourceFiles []string `json:"source_files"`
}

type catalogDeployOptions struct {
	Name             string
	Tools            []string
	Model            string
	Policies         []string
	IdentityProvider string
}

func fetchCatalogManifest(agentID, version string) (*catalogManifest, error) {
	c, err := newAPIClient()
	if err != nil {
		return nil, err
	}
	path := fmt.Sprintf("/api/catalog/%s", agentID)
	if strings.TrimSpace(version) != "" {
		path = fmt.Sprintf("/api/catalog/%s?version=%s", agentID, url.QueryEscape(strings.TrimSpace(version)))
	}
	data, err := c.Get(path)
	if err != nil {
		return nil, err
	}
	var manifest catalogManifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}
	return &manifest, nil
}

func addCSVQuery(query url.Values, key string, values []string) {
	for _, value := range values {
		trimmed := strings.TrimSpace(value)
		if trimmed != "" {
			query.Add(key, trimmed)
		}
	}
}

func catalogListQuery(search string, categories, tags, integrations, governance []string, page, pageSize int) url.Values {
	query := url.Values{}
	if strings.TrimSpace(search) != "" {
		query.Set("search", strings.TrimSpace(search))
	}
	addCSVQuery(query, "category", categories)
	addCSVQuery(query, "tag", tags)
	addCSVQuery(query, "integration", integrations)
	addCSVQuery(query, "governance", governance)
	if page > 0 {
		query.Set("page", fmt.Sprintf("%d", page))
	}
	if pageSize > 0 {
		query.Set("page_size", fmt.Sprintf("%d", pageSize))
	}
	return query
}

func printCatalogManifest(manifest *catalogManifest) {
	fmt.Printf("Name:          %s\n", manifest.Name)
	fmt.Printf("ID:            %s\n", manifest.ID)
	fmt.Printf("Version:       %s\n", manifest.Version)
	fmt.Printf("Category:      %s\n", manifest.Category)
	fmt.Printf("Summary:       %s\n", manifest.Summary)
	if manifest.DefaultModel != "" {
		fmt.Printf("Default Model: %s\n", manifest.DefaultModel)
	}
	if manifest.PublishedAt != "" {
		fmt.Printf("Published:     %s\n", manifest.PublishedAt)
	}
	if len(manifest.RequiredIntegrations) > 0 {
		fmt.Printf("Integrations:  %s\n", strings.Join(manifest.RequiredIntegrations, ", "))
	}
	if len(manifest.GovernanceTraits) > 0 {
		fmt.Printf("Governance:    %s\n", strings.Join(manifest.GovernanceTraits, ", "))
	}
	if len(manifest.DeploymentTemplate.RequiredTools) > 0 {
		fmt.Printf("Required tools:%s\n", joinedIndented(manifest.DeploymentTemplate.RequiredTools))
	}
	if len(manifest.DeploymentTemplate.RecommendedTools) > 0 {
		fmt.Printf("Recommended:%s\n", joinedIndented(manifest.DeploymentTemplate.RecommendedTools))
	}
	if manifest.DeploymentTemplate.IdentityProvider != "" {
		fmt.Printf("Identity:      %s\n", manifest.DeploymentTemplate.IdentityProvider)
	}
	if len(manifest.DeploymentTemplate.Policies) > 0 {
		fmt.Printf("Policies:%s\n", joinedIndented(manifest.DeploymentTemplate.Policies))
	}
	sourceFiles := sortedKeys(manifest.DeploymentTemplate.SourceFiles)
	if len(sourceFiles) > 0 {
		fmt.Printf("Source files:%s\n", joinedIndented(sourceFiles))
	}
	if manifest.Changelog != "" {
		fmt.Printf("Changelog:     %s\n", manifest.Changelog)
	}
}

func joinedIndented(values []string) string {
	if len(values) == 0 {
		return ""
	}
	return "\n  - " + strings.Join(values, "\n  - ")
}

func sortedKeys(m map[string]string) []string {
	keys := make([]string, 0, len(m))
	for key := range m {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func writeCatalogTemplate(targetDir string, manifest *catalogManifest, force bool) (*catalogInitSummary, error) {
	if manifest == nil {
		return nil, fmt.Errorf("catalog manifest is required")
	}
	if len(manifest.DeploymentTemplate.SourceFiles) == 0 {
		return nil, fmt.Errorf("catalog entry %q does not include source files", manifest.ID)
	}

	absTarget, err := filepath.Abs(targetDir)
	if err != nil {
		return nil, fmt.Errorf("resolve target directory: %w", err)
	}
	if err := os.MkdirAll(absTarget, 0o755); err != nil {
		return nil, fmt.Errorf("create target directory: %w", err)
	}

	sourceFiles := sortedKeys(manifest.DeploymentTemplate.SourceFiles)
	for _, relPath := range sourceFiles {
		targetPath := filepath.Join(absTarget, filepath.FromSlash(relPath))
		if !force {
			if _, err := os.Stat(targetPath); err == nil {
				return nil, fmt.Errorf("target file already exists: %s (use --force to overwrite)", targetPath)
			}
		}
		if err := os.MkdirAll(filepath.Dir(targetPath), 0o755); err != nil {
			return nil, fmt.Errorf("create directory for %s: %w", relPath, err)
		}
		if err := os.WriteFile(targetPath, []byte(manifest.DeploymentTemplate.SourceFiles[relPath]), 0o644); err != nil {
			return nil, fmt.Errorf("write %s: %w", relPath, err)
		}
	}

	manifestPath := filepath.Join(absTarget, catalogManifestFilename)
	if !force {
		if _, err := os.Stat(manifestPath); err == nil {
			return nil, fmt.Errorf("target file already exists: %s (use --force to overwrite)", manifestPath)
		}
	}
	data, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("marshal catalog manifest: %w", err)
	}
	if err := os.WriteFile(manifestPath, data, 0o644); err != nil {
		return nil, fmt.Errorf("write manifest file: %w", err)
	}

	return &catalogInitSummary{
		TargetDir:   absTarget,
		Manifest:    manifestPath,
		SourceFiles: sourceFiles,
	}, nil
}

func buildCatalogDeployPayload(manifest *catalogManifest, opts catalogDeployOptions) (map[string]any, error) {
	if manifest == nil {
		return nil, fmt.Errorf("catalog manifest is required")
	}

	agentName := strings.TrimSpace(opts.Name)
	if agentName == "" {
		agentName = strings.TrimSpace(manifest.DeploymentTemplate.AgentName)
	}
	if agentName == "" {
		agentName = strings.TrimSpace(manifest.ID)
	}
	if agentName == "" {
		return nil, fmt.Errorf("catalog manifest is missing an agent name")
	}

	llmConfigs, err := resolveCatalogLLMConfigs(manifest.DefaultModel, opts.Model)
	if err != nil {
		return nil, err
	}

	requiredTools := append([]string(nil), manifest.DeploymentTemplate.RequiredTools...)
	if len(opts.Tools) > 0 {
		requiredTools = append([]string(nil), opts.Tools...)
	}

	policies := append([]string(nil), manifest.DeploymentTemplate.Policies...)
	if len(opts.Policies) > 0 {
		policies = append([]string(nil), opts.Policies...)
	}

	identityProvider := strings.TrimSpace(opts.IdentityProvider)
	if identityProvider == "" {
		identityProvider = strings.TrimSpace(manifest.DeploymentTemplate.IdentityProvider)
	}

	payload := map[string]any{
		"agent_name":   agentName,
		"source_files": manifest.DeploymentTemplate.SourceFiles,
	}
	if strings.TrimSpace(manifest.DeploymentTemplate.SystemPrompt) != "" {
		payload["system_prompt"] = strings.TrimSpace(manifest.DeploymentTemplate.SystemPrompt)
	}
	if len(requiredTools) > 0 {
		payload["required_tools"] = requiredTools
	}
	if len(policies) > 0 {
		payload["policies"] = policies
	}
	if identityProvider != "" {
		payload["identity_provider"] = identityProvider
	}
	if len(llmConfigs) > 0 {
		payload["llm_configs"] = llmConfigs
	}
	return payload, nil
}

func resolveCatalogLLMConfigs(defaultModel, modelFlag string) ([]map[string]string, error) {
	modelValue := strings.TrimSpace(modelFlag)
	if modelValue == "" {
		modelValue = strings.TrimSpace(defaultModel)
		if modelValue != "" && !strings.Contains(modelValue, "/") {
			modelValue = "openai/" + modelValue
		}
	}
	if modelValue == "" {
		return nil, nil
	}
	parts := strings.SplitN(modelValue, "/", 2)
	if len(parts) != 2 || strings.TrimSpace(parts[0]) == "" || strings.TrimSpace(parts[1]) == "" {
		return nil, fmt.Errorf("catalog deploy model must be in provider/model format; got %q", modelValue)
	}
	return []map[string]string{{
		"provider": strings.TrimSpace(parts[0]),
		"model":    strings.TrimSpace(parts[1]),
		"role":     "default",
	}}, nil
}
