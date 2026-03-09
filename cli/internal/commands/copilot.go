package commands

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/runagents/runagents/cli/internal/client"
	"github.com/runagents/runagents/cli/internal/config"
	"github.com/spf13/cobra"
)

const (
	copilotContextPage = "cli"
	copilotMaxFiles    = 80
	copilotMaxFileSize = 256 * 1024
	copilotMaxTotal    = 2 * 1024 * 1024
)

var (
	reCopilotAgentAs    = regexp.MustCompile(`(?i)\bas\s+([a-z0-9][a-z0-9-]{1,62})\b`)
	reCopilotAgentNamed = regexp.MustCompile(`(?i)\bnamed\s+([a-z0-9][a-z0-9-]{1,62})\b`)
	reCopilotHTTPStatus = regexp.MustCompile(`HTTP\s+(\d{3})`)

	copilotIgnoreDirs = map[string]struct{}{
		".git":         {},
		".venv":        {},
		"venv":         {},
		"node_modules": {},
		"dist":         {},
		"build":        {},
		"target":       {},
		"out":          {},
		"bin":          {},
		"obj":          {},
		"coverage":     {},
		"__pycache__":  {},
		".runagents":   {},
	}

	copilotSourceNames = map[string]struct{}{
		"dockerfile":        {},
		"makefile":          {},
		"readme.md":         {},
		"requirements.txt":  {},
		"pyproject.toml":    {},
		"poetry.lock":       {},
		"uv.lock":           {},
		"package.json":      {},
		"package-lock.json": {},
		"pnpm-lock.yaml":    {},
		"yarn.lock":         {},
		"go.mod":            {},
		"go.sum":            {},
		"cargo.toml":        {},
		"cargo.lock":        {},
		"pom.xml":           {},
		"build.gradle":      {},
		"settings.gradle":   {},
	}

	copilotSourceExtensions = map[string]struct{}{
		".py":    {},
		".js":    {},
		".jsx":   {},
		".mjs":   {},
		".cjs":   {},
		".ts":    {},
		".tsx":   {},
		".go":    {},
		".java":  {},
		".kt":    {},
		".rb":    {},
		".php":   {},
		".rs":    {},
		".cs":    {},
		".swift": {},
		".scala": {},
		".sh":    {},
		".bash":  {},
		".zsh":   {},
		".ps1":   {},
		".yaml":  {},
		".yml":   {},
		".toml":  {},
		".json":  {},
		".ini":   {},
		".cfg":   {},
		".conf":  {},
		".sql":   {},
		".proto": {},
	}
)

type copilotMessagePayload struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type copilotChatRequestPayload struct {
	Messages         []copilotMessagePayload `json:"messages,omitempty"`
	Context          map[string]any          `json:"context"`
	SessionID        string                  `json:"session_id,omitempty"`
	ConfirmActionIDs []string                `json:"confirm_action_ids,omitempty"`
	RejectActionIDs  []string                `json:"reject_action_ids,omitempty"`
}

type copilotPendingActionPayload struct {
	ID          string         `json:"id"`
	Function    string         `json:"function"`
	Description string         `json:"description"`
	Risk        string         `json:"risk"`
	Preview     map[string]any `json:"preview,omitempty"`
	Status      string         `json:"status"`
	Error       string         `json:"error,omitempty"`
}

type copilotExecutedActionPayload struct {
	ID          string `json:"id"`
	Function    string `json:"function"`
	Status      string `json:"status"`
	ResourceRef string `json:"resource_ref,omitempty"`
	Error       string `json:"error,omitempty"`
}

type copilotChatResponsePayload struct {
	Content         string                         `json:"content"`
	SessionID       string                         `json:"session_id,omitempty"`
	PendingActions  []copilotPendingActionPayload  `json:"pending_actions,omitempty"`
	ExecutedActions []copilotExecutedActionPayload `json:"executed_actions,omitempty"`
}

type workflowArtifactResponse struct {
	ID string `json:"id"`
}

type deployDraftResponse struct {
	ID string `json:"id"`
}

type copilotDoctorCheck struct {
	Name    string `json:"name"`
	Status  string `json:"status"`
	Details string `json:"details"`
}

func newCopilotCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "copilot",
		Short: "Interact with RunAgents Copilot in natural language",
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			return ensureCopilotEnabled()
		},
	}

	cmd.AddCommand(newCopilotChatCmd())
	cmd.AddCommand(newCopilotPendingCmd())
	cmd.AddCommand(newCopilotConfirmCmd())
	cmd.AddCommand(newCopilotRejectCmd())
	cmd.AddCommand(newCopilotDoctorCmd())
	cmd.AddCommand(newCopilotStatusCmd())
	cmd.AddCommand(newCopilotShellCmd())
	cmd.AddCommand(newCopilotResetCmd())
	return cmd
}

func ensureCopilotEnabled() error {
	mode, err := resolvedAssistantMode()
	if err != nil {
		return err
	}
	if mode != config.AssistantModeRunAgents {
		return fmt.Errorf("copilot commands are disabled when assistant-mode=%q; set 'runagents config set assistant-mode runagents' to enable", mode)
	}
	return nil
}

func newCopilotChatCmd() *cobra.Command {
	var assumeYes bool
	cmd := &cobra.Command{
		Use:   "chat <prompt>",
		Short: "Send a natural-language prompt to Copilot",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prompt := strings.TrimSpace(strings.Join(args, " "))
			if prompt == "" {
				return fmt.Errorf("prompt cannot be empty")
			}
			return runCopilotChatPrompt(prompt, false, assumeYes)
		},
	}
	cmd.Flags().BoolVarP(&assumeYes, "yes", "y", false, "Auto-confirm local deploy-assist staging when prompt targets current folder")
	return cmd
}

func newCopilotDoctorCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "Run local and API readiness checks for Copilot CLI",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCopilotDoctor()
		},
	}
}

func newCopilotPendingCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "pending",
		Short: "List pending staged Copilot actions",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCopilotPendingFetch()
		},
	}
}

func newCopilotConfirmCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "confirm <action_id>",
		Short: "Confirm a staged Copilot action",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCopilotResolveAction(args[0], true)
		},
	}
}

func newCopilotRejectCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "reject <action_id>",
		Short: "Reject a staged Copilot action",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCopilotResolveAction(args[0], false)
		},
	}
}

func newCopilotShellCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "shell",
		Short: "Start interactive Copilot shell",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCopilotShell()
		},
	}
}

func newCopilotStatusCmd() *cobra.Command {
	var refresh bool
	cmd := &cobra.Command{
		Use:   "status",
		Short: "Show local Copilot session status for this project",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCopilotStatus(refresh)
		},
	}
	cmd.Flags().BoolVar(&refresh, "refresh", false, "Refresh pending actions from API for active session")
	return cmd
}

func newCopilotResetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "reset-session",
		Short: "Reset local Copilot session and memory files for this project",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			cwd, err := os.Getwd()
			if err != nil {
				return fmt.Errorf("failed to resolve current directory: %w", err)
			}
			if err := config.ResetProjectState(cwd); err != nil {
				return err
			}
			fmt.Println("Local Copilot session reset for current project.")
			return nil
		},
	}
}

func runDefaultInteractiveShell() error {
	return runCopilotShell()
}

func runCopilotShell() error {
	fmt.Println("RunAgents Copilot shell")
	fmt.Println("Type natural language requests, or use /help, /doctor, /status, /pending, /confirm <id>, /reject <id>, /reset, /exit")

	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print("runagents> ")
		if !scanner.Scan() {
			fmt.Println()
			return nil
		}
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		switch {
		case line == "/exit" || line == "exit" || line == "quit":
			return nil
		case line == "/help":
			fmt.Println("/doctor, /status, /pending, /confirm <id>, /reject <id>, /reset, /exit")
			continue
		case line == "/doctor":
			if err := runCopilotDoctor(); err != nil {
				fmt.Printf("error: %v\n", err)
			}
			continue
		case line == "/status":
			if err := runCopilotStatus(false); err != nil {
				fmt.Printf("error: %v\n", err)
			}
			continue
		case line == "/pending":
			if err := runCopilotPendingFetch(); err != nil {
				fmt.Printf("error: %v\n", err)
			}
			continue
		case strings.HasPrefix(line, "/confirm "):
			actionID := strings.TrimSpace(strings.TrimPrefix(line, "/confirm "))
			if actionID == "" {
				fmt.Println("usage: /confirm <action_id>")
				continue
			}
			if err := runCopilotResolveAction(actionID, true); err != nil {
				fmt.Printf("error: %v\n", err)
			}
			continue
		case strings.HasPrefix(line, "/reject "):
			actionID := strings.TrimSpace(strings.TrimPrefix(line, "/reject "))
			if actionID == "" {
				fmt.Println("usage: /reject <action_id>")
				continue
			}
			if err := runCopilotResolveAction(actionID, false); err != nil {
				fmt.Printf("error: %v\n", err)
			}
			continue
		case line == "/reset":
			cwd, err := os.Getwd()
			if err != nil {
				fmt.Printf("error: %v\n", err)
				continue
			}
			if err := config.ResetProjectState(cwd); err != nil {
				fmt.Printf("error: %v\n", err)
				continue
			}
			fmt.Println("Session reset.")
			continue
		default:
			if err := runCopilotChatPrompt(line, true, false); err != nil {
				fmt.Printf("error: %v\n", err)
			}
		}
	}
}

func runCopilotDoctor() error {
	endpoint, apiKey, namespace, err := resolvedAPISettings()
	if err != nil {
		return err
	}

	checks := make([]copilotDoctorCheck, 0, 8)
	failures := 0

	endpointTrimmed := strings.TrimSpace(endpoint)
	if endpointTrimmed == "" {
		checks = append(checks, copilotDoctorCheck{
			Name:    "config.endpoint",
			Status:  "fail",
			Details: "Endpoint is not configured. Set via 'runagents config set endpoint <url>' or --endpoint.",
		})
		failures++
	} else if _, parseErr := url.ParseRequestURI(endpointTrimmed); parseErr != nil {
		checks = append(checks, copilotDoctorCheck{
			Name:    "config.endpoint",
			Status:  "fail",
			Details: fmt.Sprintf("Endpoint is not a valid URL: %v", parseErr),
		})
		failures++
	} else {
		checks = append(checks, copilotDoctorCheck{
			Name:    "config.endpoint",
			Status:  "pass",
			Details: endpointTrimmed,
		})
	}

	namespaceTrimmed := strings.TrimSpace(namespace)
	if namespaceTrimmed == "" {
		checks = append(checks, copilotDoctorCheck{
			Name:    "config.namespace",
			Status:  "fail",
			Details: "Namespace is not configured. Set via 'runagents config set namespace <name>' or --namespace.",
		})
		failures++
	} else {
		checks = append(checks, copilotDoctorCheck{
			Name:    "config.namespace",
			Status:  "pass",
			Details: namespaceTrimmed,
		})
	}

	apiKeyTrimmed := strings.TrimSpace(apiKey)
	if apiKeyTrimmed == "" {
		checks = append(checks, copilotDoctorCheck{
			Name:    "config.api_key",
			Status:  "warn",
			Details: "API key is empty. Authenticated API operations may fail. Set via 'runagents config set api-key <key>' or --api-key.",
		})
	} else {
		checks = append(checks, copilotDoctorCheck{
			Name:    "config.api_key",
			Status:  "pass",
			Details: maskAPIKey(apiKeyTrimmed),
		})
	}

	if endpointTrimmed != "" {
		statusCode, probeErr := probeEndpointReachability(endpointTrimmed)
		if probeErr != nil {
			checks = append(checks, copilotDoctorCheck{
				Name:    "network.endpoint_reachability",
				Status:  "fail",
				Details: probeErr.Error(),
			})
			failures++
		} else {
			checks = append(checks, copilotDoctorCheck{
				Name:    "network.endpoint_reachability",
				Status:  "pass",
				Details: fmt.Sprintf("HTTP %d from %s", statusCode, strings.TrimRight(endpointTrimmed, "/")+"/"),
			})
		}
	}

	if endpointTrimmed != "" && namespaceTrimmed != "" && apiKeyTrimmed != "" {
		c := client.NewClient(endpointTrimmed, apiKeyTrimmed, namespaceTrimmed)
		if _, getErr := c.Get("/api/tools"); getErr != nil {
			statusCode := extractHTTPStatus(getErr)
			status := "warn"
			if statusCode == 0 || statusCode >= 500 || statusCode == 401 || statusCode == 403 || statusCode == 404 {
				status = "fail"
				failures++
			}
			details := fmt.Sprintf("GET /api/tools failed: %v", getErr)
			if statusCode == 401 || statusCode == 403 {
				details = "Authentication/authorization failed for GET /api/tools. Check api key and namespace."
			}
			if statusCode == 404 {
				details = "GET /api/tools returned 404. Verify endpoint points to RunAgents governance API."
			}
			checks = append(checks, copilotDoctorCheck{
				Name:    "api.auth_probe",
				Status:  status,
				Details: details,
			})
		} else {
			checks = append(checks, copilotDoctorCheck{
				Name:    "api.auth_probe",
				Status:  "pass",
				Details: "GET /api/tools succeeded with current credentials and namespace.",
			})
		}
	}

	cwd, cwdErr := os.Getwd()
	if cwdErr == nil {
		state, stateErr := config.LoadProjectState(cwd)
		if stateErr != nil {
			checks = append(checks, copilotDoctorCheck{
				Name:    "project.session_state",
				Status:  "warn",
				Details: stateErr.Error(),
			})
		} else if strings.TrimSpace(state.SessionID) == "" {
			checks = append(checks, copilotDoctorCheck{
				Name:    "project.session_state",
				Status:  "warn",
				Details: "No active local Copilot session in this project yet.",
			})
		} else {
			checks = append(checks, copilotDoctorCheck{
				Name:    "project.session_state",
				Status:  "pass",
				Details: fmt.Sprintf("session_id=%s", strings.TrimSpace(state.SessionID)),
			})
		}
	}

	if isJSONOutput() {
		payload := map[string]any{
			"ok":       failures == 0,
			"checks":   checks,
			"failures": failures,
		}
		raw, marshalErr := json.Marshal(payload)
		if marshalErr != nil {
			return fmt.Errorf("failed to encode doctor result: %w", marshalErr)
		}
		fmt.Println(string(raw))
	} else {
		fmt.Println("RunAgents Copilot doctor")
		for _, check := range checks {
			fmt.Printf("- [%s] %s: %s\n", strings.ToUpper(check.Status), check.Name, check.Details)
		}
		if failures == 0 {
			fmt.Println("Doctor result: OK")
		} else {
			fmt.Printf("Doctor result: %d failing checks\n", failures)
		}
	}

	if failures > 0 {
		return fmt.Errorf("doctor found %d failing checks", failures)
	}
	return nil
}

func runCopilotStatus(refresh bool) error {
	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("failed to resolve current directory: %w", err)
	}
	state, err := config.LoadProjectState(cwd)
	if err != nil {
		return err
	}

	if refresh && strings.TrimSpace(state.SessionID) != "" {
		c, err := newAPIClient()
		if err != nil {
			return err
		}
		req := copilotChatRequestPayload{
			Context: map[string]any{
				"currentPage": copilotContextPage,
			},
			SessionID: state.SessionID,
		}
		_, resp, err := callCopilot(c, req)
		if err != nil {
			return err
		}
		state.SessionID = firstNonEmpty(resp.SessionID, state.SessionID)
		state.PendingActionIDs = collectPendingActionIDs(resp.PendingActions)
		state.LastResponse = strings.TrimSpace(resp.Content)
		state.UpdatedAt = time.Now().UTC()
		if err := config.SaveProjectState(cwd, state); err != nil {
			return err
		}
	}

	statePath := filepath.Join(cwd, ".runagents", "state.json")
	memoryPath := filepath.Join(cwd, ".runagents", "memory.md")
	nextCmd := ""
	if len(state.PendingActionIDs) > 0 {
		nextCmd = "runagents copilot confirm " + state.PendingActionIDs[0]
	}

	if isJSONOutput() {
		payload := map[string]any{
			"project_path":        cwd,
			"session_id":          strings.TrimSpace(state.SessionID),
			"pending_action_ids":  state.PendingActionIDs,
			"pending_count":       len(state.PendingActionIDs),
			"last_prompt":         state.LastPrompt,
			"last_response":       state.LastResponse,
			"updated_at":          state.UpdatedAt,
			"state_file":          statePath,
			"memory_file":         memoryPath,
			"next_suggested_cmd":  nextCmd,
			"refreshed_from_api":  refresh,
			"has_active_session":  strings.TrimSpace(state.SessionID) != "",
			"has_pending_actions": len(state.PendingActionIDs) > 0,
		}
		data, err := json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("failed to encode status output: %w", err)
		}
		fmt.Println(string(data))
		return nil
	}

	fmt.Printf("Project:           %s\n", cwd)
	if strings.TrimSpace(state.SessionID) == "" {
		fmt.Println("Session:           (none)")
	} else {
		fmt.Printf("Session:           %s\n", state.SessionID)
	}
	if state.UpdatedAt.IsZero() {
		fmt.Println("Last Updated:      (unknown)")
	} else {
		fmt.Printf("Last Updated:      %s\n", state.UpdatedAt.Format(time.RFC3339))
	}
	fmt.Printf("Pending Actions:   %d\n", len(state.PendingActionIDs))
	if len(state.PendingActionIDs) > 0 {
		fmt.Printf("Next Suggestion:   %s\n", nextCmd)
	}
	fmt.Printf("State File:        %s\n", statePath)
	fmt.Printf("Memory File:       %s\n", memoryPath)
	return nil
}

func runCopilotChatPrompt(prompt string, interactive, assumeYes bool) error {
	c, cwd, state, err := copilotCommandContext()
	if err != nil {
		return err
	}

	finalPrompt, prepNote, err := maybePrepareDeployDraftFromCurrentFolder(c, prompt, cwd, interactive, assumeYes)
	if err != nil {
		return err
	}
	if prepNote != "" && !isJSONOutput() {
		fmt.Println(prepNote)
	}

	req := copilotChatRequestPayload{
		Messages: []copilotMessagePayload{
			{Role: "user", Content: finalPrompt},
		},
		Context: map[string]any{
			"currentPage": copilotContextPage,
		},
		SessionID: strings.TrimSpace(state.SessionID),
	}
	raw, resp, err := callCopilot(c, req)
	if err != nil {
		return err
	}

	state.SessionID = firstNonEmpty(resp.SessionID, state.SessionID)
	state.LastPrompt = prompt
	state.LastResponse = strings.TrimSpace(resp.Content)
	state.PendingActionIDs = collectPendingActionIDs(resp.PendingActions)
	state.UpdatedAt = time.Now().UTC()
	if err := config.SaveProjectState(cwd, state); err != nil {
		return err
	}

	nextCmd := ""
	if len(state.PendingActionIDs) > 0 {
		nextCmd = "runagents copilot confirm " + state.PendingActionIDs[0]
	}
	if err := config.SaveProjectMemory(cwd, config.MemorySnapshot{
		CurrentGoal:          prompt,
		SessionID:            state.SessionID,
		RecentSummary:        memorySummaryFromResponse(resp),
		PendingActionIDs:     state.PendingActionIDs,
		NextSuggestedCommand: nextCmd,
		UpdatedAt:            state.UpdatedAt,
	}); err != nil {
		return err
	}

	if isJSONOutput() {
		fmt.Println(string(raw))
		return nil
	}
	printCopilotResponse(resp, interactive)
	return nil
}

func runCopilotPendingFetch() error {
	c, cwd, state, err := copilotCommandContext()
	if err != nil {
		return err
	}
	if strings.TrimSpace(state.SessionID) == "" {
		return fmt.Errorf("no active copilot session in this project; start with 'runagents copilot chat \"...\"'")
	}
	req := copilotChatRequestPayload{
		Context: map[string]any{
			"currentPage": copilotContextPage,
		},
		SessionID: state.SessionID,
	}
	raw, resp, err := callCopilot(c, req)
	if err != nil {
		return err
	}
	state.SessionID = firstNonEmpty(resp.SessionID, state.SessionID)
	state.PendingActionIDs = collectPendingActionIDs(resp.PendingActions)
	state.LastResponse = strings.TrimSpace(resp.Content)
	state.UpdatedAt = time.Now().UTC()
	if err := config.SaveProjectState(cwd, state); err != nil {
		return err
	}
	if isJSONOutput() {
		fmt.Println(string(raw))
		return nil
	}
	printCopilotResponse(resp, false)
	return nil
}

func runCopilotResolveAction(actionID string, approve bool) error {
	actionID = strings.TrimSpace(actionID)
	if actionID == "" {
		return fmt.Errorf("action_id is required")
	}
	c, cwd, state, err := copilotCommandContext()
	if err != nil {
		return err
	}
	if strings.TrimSpace(state.SessionID) == "" {
		return fmt.Errorf("no active copilot session in this project; start with 'runagents copilot chat \"...\"'")
	}

	req := copilotChatRequestPayload{
		Context: map[string]any{
			"currentPage": copilotContextPage,
		},
		SessionID: state.SessionID,
	}
	if approve {
		req.ConfirmActionIDs = []string{actionID}
	} else {
		req.RejectActionIDs = []string{actionID}
	}

	raw, resp, err := callCopilot(c, req)
	if err != nil {
		return err
	}
	state.SessionID = firstNonEmpty(resp.SessionID, state.SessionID)
	state.PendingActionIDs = collectPendingActionIDs(resp.PendingActions)
	state.LastResponse = strings.TrimSpace(resp.Content)
	state.UpdatedAt = time.Now().UTC()
	if err := config.SaveProjectState(cwd, state); err != nil {
		return err
	}
	if isJSONOutput() {
		fmt.Println(string(raw))
		return nil
	}
	printCopilotResponse(resp, false)
	return nil
}

func copilotCommandContext() (*client.Client, string, *config.ProjectState, error) {
	c, err := newAPIClient()
	if err != nil {
		return nil, "", nil, err
	}
	cwd, err := os.Getwd()
	if err != nil {
		return nil, "", nil, fmt.Errorf("failed to resolve current directory: %w", err)
	}
	state, err := config.LoadProjectState(cwd)
	if err != nil {
		return nil, "", nil, err
	}
	return c, cwd, state, nil
}

func callCopilot(c *client.Client, req copilotChatRequestPayload) ([]byte, copilotChatResponsePayload, error) {
	data, err := c.Post("/api/copilot/chat", req)
	if err != nil {
		return nil, copilotChatResponsePayload{}, err
	}
	var resp copilotChatResponsePayload
	if err := json.Unmarshal(data, &resp); err != nil {
		return nil, copilotChatResponsePayload{}, fmt.Errorf("failed to decode copilot response: %w", err)
	}
	return data, resp, nil
}

func printCopilotResponse(resp copilotChatResponsePayload, interactive bool) {
	content := strings.TrimSpace(resp.Content)
	if content != "" {
		fmt.Println(content)
	}
	if len(resp.PendingActions) > 0 {
		fmt.Println()
		fmt.Println("Pending actions:")
		for _, action := range resp.PendingActions {
			fmt.Printf("- %s [%s] %s (risk: %s)\n", action.ID, action.Function, action.Description, strings.ToLower(strings.TrimSpace(action.Risk)))
		}
		fmt.Println("Use: runagents copilot confirm <action_id> or runagents copilot reject <action_id>")
	}
	if len(resp.ExecutedActions) > 0 {
		fmt.Println()
		fmt.Println("Executed actions:")
		for _, action := range resp.ExecutedActions {
			line := fmt.Sprintf("- %s [%s] status=%s", action.ID, action.Function, action.Status)
			if action.ResourceRef != "" {
				line += " resource=" + action.ResourceRef
			}
			if action.Error != "" {
				line += " error=" + action.Error
			}
			fmt.Println(line)
		}
	}
	if interactive {
		fmt.Println()
	}
}

func collectPendingActionIDs(actions []copilotPendingActionPayload) []string {
	if len(actions) == 0 {
		return nil
	}
	out := make([]string, 0, len(actions))
	for _, action := range actions {
		if strings.TrimSpace(action.ID) != "" {
			out = append(out, strings.TrimSpace(action.ID))
		}
	}
	sort.Strings(out)
	return out
}

func memorySummaryFromResponse(resp copilotChatResponsePayload) string {
	content := strings.TrimSpace(resp.Content)
	if content != "" {
		return content
	}
	if len(resp.PendingActions) > 0 {
		return fmt.Sprintf("%d pending actions staged", len(resp.PendingActions))
	}
	if len(resp.ExecutedActions) > 0 {
		return fmt.Sprintf("%d actions processed", len(resp.ExecutedActions))
	}
	return "no updates"
}

func probeEndpointReachability(endpoint string) (int, error) {
	u := strings.TrimSpace(endpoint)
	if u == "" {
		return 0, fmt.Errorf("endpoint is empty")
	}
	if _, err := url.ParseRequestURI(u); err != nil {
		return 0, fmt.Errorf("invalid endpoint URL: %w", err)
	}
	target := strings.TrimRight(u, "/") + "/"
	req, err := http.NewRequest(http.MethodGet, target, nil)
	if err != nil {
		return 0, fmt.Errorf("failed to prepare request: %w", err)
	}
	hc := &http.Client{Timeout: 5 * time.Second}
	resp, err := hc.Do(req)
	if err != nil {
		return 0, fmt.Errorf("failed to reach endpoint %s: %w", target, err)
	}
	defer resp.Body.Close()
	return resp.StatusCode, nil
}

func extractHTTPStatus(err error) int {
	if err == nil {
		return 0
	}
	matches := reCopilotHTTPStatus.FindStringSubmatch(err.Error())
	if len(matches) < 2 {
		return 0
	}
	code, convErr := strconv.Atoi(matches[1])
	if convErr != nil {
		return 0
	}
	return code
}

func shouldProceedWithDeployAssist(interactive, assumeYes bool, input io.Reader, output io.Writer) (bool, error) {
	if assumeYes {
		return true, nil
	}
	if !interactive {
		return false, fmt.Errorf("deploy assist needs confirmation in non-interactive mode; rerun with 'runagents copilot chat --yes \"...\"'")
	}
	if input == nil {
		input = os.Stdin
	}
	if output == nil {
		output = os.Stdout
	}
	fmt.Fprint(output, "This will upload selected local files to RunAgents as an artifact draft. Proceed? [y/N]: ")
	scanner := bufio.NewScanner(input)
	if !scanner.Scan() {
		if err := scanner.Err(); err != nil {
			return false, err
		}
		return false, nil
	}
	answer := strings.ToLower(strings.TrimSpace(scanner.Text()))
	return answer == "y" || answer == "yes", nil
}

func maybePrepareDeployDraftFromCurrentFolder(c *client.Client, prompt, cwd string, interactive, assumeYes bool) (string, string, error) {
	trimmed := strings.TrimSpace(prompt)
	if !shouldUseCurrentFolderDeployAssist(trimmed) {
		return trimmed, "", nil
	}
	proceed, err := shouldProceedWithDeployAssist(interactive, assumeYes, os.Stdin, os.Stdout)
	if err != nil {
		return "", "", err
	}
	if !proceed {
		return trimmed, "Skipped local folder deploy preparation.", nil
	}

	files, err := collectLocalSourceFiles(cwd)
	if err != nil {
		return "", "", err
	}
	if len(files) == 0 {
		return "", "", fmt.Errorf("no deployable source files found in current folder")
	}

	artifactPayload := map[string]any{
		"source_type":  "code",
		"build_mode":   "native",
		"source_files": files,
	}
	artifactRaw, err := c.Post("/api/workflow-artifacts", artifactPayload)
	if err != nil {
		return "", "", fmt.Errorf("failed to create workflow artifact from local folder: %w", err)
	}
	var artifact workflowArtifactResponse
	if err := json.Unmarshal(artifactRaw, &artifact); err != nil {
		return "", "", fmt.Errorf("failed to decode workflow artifact response: %w", err)
	}
	if strings.TrimSpace(artifact.ID) == "" {
		return "", "", fmt.Errorf("workflow artifact response did not include id")
	}

	draftPayload := map[string]any{
		"artifact_id": artifact.ID,
		"source_type": "code",
		"step":        "deploy",
	}
	draftRaw, err := c.Post("/api/deploy-drafts", draftPayload)
	if err != nil {
		return "", "", fmt.Errorf("failed to create deploy draft from artifact %s: %w", artifact.ID, err)
	}
	var draft deployDraftResponse
	if err := json.Unmarshal(draftRaw, &draft); err != nil {
		return "", "", fmt.Errorf("failed to decode deploy draft response: %w", err)
	}
	if strings.TrimSpace(draft.ID) == "" {
		return "", "", fmt.Errorf("deploy draft response did not include id")
	}

	agentName := inferAgentNameFromPromptOrDir(trimmed, cwd)
	rewrittenPrompt := fmt.Sprintf("deploy draft %s as %s", draft.ID, agentName)
	note := fmt.Sprintf("Prepared local folder deploy context: artifact=%s draft=%s agent=%s", artifact.ID, draft.ID, agentName)
	return rewrittenPrompt, note, nil
}

func shouldUseCurrentFolderDeployAssist(prompt string) bool {
	lower := strings.ToLower(strings.TrimSpace(prompt))
	if lower == "" {
		return false
	}
	if !strings.Contains(lower, "deploy") {
		return false
	}
	if strings.Contains(lower, "draft ") {
		return false
	}
	markers := []string{
		"this folder",
		"current folder",
		"this repo",
		"this repository",
		"this project",
		"local folder",
		"from here",
		"this codebase",
	}
	for _, marker := range markers {
		if strings.Contains(lower, marker) {
			return true
		}
	}
	return false
}

func collectLocalSourceFiles(cwd string) (map[string]string, error) {
	files := make(map[string]string)
	totalBytes := 0
	err := filepath.WalkDir(cwd, func(path string, d os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		name := d.Name()
		if d.IsDir() {
			if _, skip := copilotIgnoreDirs[name]; skip && path != cwd {
				return filepath.SkipDir
			}
			return nil
		}
		if _, excluded := copilotIgnoreDirs[name]; excluded {
			return nil
		}
		if d.Type()&os.ModeSymlink != 0 {
			return nil
		}

		nameLower := strings.ToLower(name)
		extLower := strings.ToLower(filepath.Ext(name))
		_, includeName := copilotSourceNames[nameLower]
		_, includeExt := copilotSourceExtensions[extLower]
		includeFile := includeName || includeExt
		if !includeFile {
			return nil
		}
		if len(files) >= copilotMaxFiles {
			return fmt.Errorf("too many source files; max %d", copilotMaxFiles)
		}
		info, err := d.Info()
		if err != nil {
			return err
		}
		if info.Size() > copilotMaxFileSize {
			return nil
		}
		totalBytes += int(info.Size())
		if totalBytes > copilotMaxTotal {
			return fmt.Errorf("total selected source size exceeds %d bytes", copilotMaxTotal)
		}

		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(cwd, path)
		if err != nil {
			return err
		}
		files[filepath.ToSlash(rel)] = string(data)
		return nil
	})
	if err != nil {
		return nil, err
	}
	return files, nil
}

func inferAgentNameFromPromptOrDir(prompt, cwd string) string {
	matches := reCopilotAgentAs.FindStringSubmatch(prompt)
	if len(matches) >= 2 {
		return sanitizeAgentName(matches[1])
	}
	matches = reCopilotAgentNamed.FindStringSubmatch(prompt)
	if len(matches) >= 2 {
		return sanitizeAgentName(matches[1])
	}
	base := filepath.Base(cwd)
	base = sanitizeAgentName(base)
	if base == "" {
		base = "agent"
	}
	if !strings.HasSuffix(base, "-agent") {
		base += "-agent"
	}
	return sanitizeAgentName(base)
}

func sanitizeAgentName(raw string) string {
	raw = strings.ToLower(strings.TrimSpace(raw))
	if raw == "" {
		return ""
	}
	var b strings.Builder
	prevDash := false
	for _, r := range raw {
		valid := (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9')
		if valid {
			b.WriteRune(r)
			prevDash = false
			continue
		}
		if !prevDash {
			b.WriteRune('-')
			prevDash = true
		}
	}
	out := strings.Trim(b.String(), "-")
	if out == "" {
		return ""
	}
	if len(out) > 63 {
		out = strings.Trim(out[:63], "-")
	}
	return out
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return strings.TrimSpace(value)
		}
	}
	return ""
}
