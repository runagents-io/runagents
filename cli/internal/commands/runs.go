package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"sort"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

type cliRun struct {
	ID              string    `json:"id"`
	ConversationID  string    `json:"conversation_id"`
	AgentID         string    `json:"agent_id"`
	AgentUID        string    `json:"agent_uid,omitempty"`
	Namespace       string    `json:"namespace"`
	UserID          string    `json:"user_id"`
	SurfaceTurnID   string    `json:"surface_turn_id,omitempty"`
	Status          string    `json:"status"`
	BlockedActionID string    `json:"blocked_action_id,omitempty"`
	InitialMessage  string    `json:"initial_message,omitempty"`
	InvokeURL       string    `json:"invoke_url,omitempty"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

type cliRunEvent struct {
	EventID     string         `json:"event_id"`
	RunID       string         `json:"run_id"`
	Seq         int            `json:"seq"`
	Type        string         `json:"type"`
	PayloadHash string         `json:"payload_hash,omitempty"`
	Actor       string         `json:"actor,omitempty"`
	Data        map[string]any `json:"data,omitempty"`
	Timestamp   time.Time      `json:"timestamp"`
}

type cliRunTimelineEntry struct {
	Seq       int            `json:"seq,omitempty"`
	Type      string         `json:"type"`
	Actor     string         `json:"actor,omitempty"`
	Summary   string         `json:"summary"`
	Timestamp time.Time      `json:"timestamp"`
	Data      map[string]any `json:"data,omitempty"`
}

type cliRunExport struct {
	Run      cliRun                `json:"run"`
	Events   []cliRunEvent         `json:"events"`
	Timeline []cliRunTimelineEntry `json:"timeline"`
}

type runFilters struct {
	AgentID        string
	Status         string
	UserID         string
	ConversationID string
	Limit          int
}

type runEventFilters struct {
	Type  string
	Limit int
}

type runAPIClient interface {
	Get(string) ([]byte, error)
	GetWithQuery(string, url.Values) ([]byte, error)
}

func newRunsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "runs",
		Short: "Inspect and debug agent runs",
	}

	cmd.AddCommand(newRunsListCmd())
	cmd.AddCommand(newRunsGetCmd())
	cmd.AddCommand(newRunsEventsCmd())
	cmd.AddCommand(newRunsTimelineCmd())
	cmd.AddCommand(newRunsWaitCmd())
	cmd.AddCommand(newRunsExportCmd())

	return cmd
}

func newRunsListCmd() *cobra.Command {
	filters := runFilters{Limit: 50}

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List runs with operator-friendly filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			query := url.Values{}
			if strings.TrimSpace(filters.AgentID) != "" {
				query.Set("agent_id", strings.TrimSpace(filters.AgentID))
			}
			if strings.TrimSpace(filters.Status) != "" {
				query.Set("status", strings.TrimSpace(filters.Status))
			}

			runs, err := fetchRuns(c, query)
			if err != nil {
				return err
			}
			runs = filterRuns(runs, filters)

			if isJSONOutput() {
				return printJSONValue(runs)
			}
			if len(runs) == 0 {
				fmt.Println("No runs found.")
				return nil
			}

			table := newTable("ID", "AGENT", "USER", "STATUS", "UPDATED")
			for _, run := range runs {
				table.Append([]string{
					run.ID,
					run.AgentID,
					run.UserID,
					run.Status,
					formatRunTime(run.UpdatedAt),
				})
			}
			table.Render()
			return nil
		},
	}

	cmd.Flags().StringVar(&filters.AgentID, "agent", "", "Filter runs by agent name")
	cmd.Flags().StringVar(&filters.Status, "status", "", "Filter runs by status")
	cmd.Flags().StringVar(&filters.UserID, "user", "", "Filter runs by user ID")
	cmd.Flags().StringVar(&filters.ConversationID, "conversation", "", "Filter runs by conversation ID")
	cmd.Flags().IntVar(&filters.Limit, "limit", 50, "Maximum number of runs to display (0 for all)")

	return cmd
}

func newRunsGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <run-id>",
		Short: "Get details for a specific run",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			run, err := fetchRun(c, args[0])
			if err != nil {
				return err
			}
			if isJSONOutput() {
				return printJSONValue(run)
			}
			printRun(*run)
			return nil
		},
	}
}

func newRunsEventsCmd() *cobra.Command {
	filters := runEventFilters{Limit: 100}

	cmd := &cobra.Command{
		Use:   "events <run-id>",
		Short: "Show run events with meaningful summaries",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			events, err := fetchRunEvents(c, args[0], 0)
			if err != nil {
				return err
			}
			events = filterRunEvents(events, filters)
			if isJSONOutput() {
				return printJSONValue(events)
			}
			if len(events) == 0 {
				fmt.Println("No run events found.")
				return nil
			}
			table := newTable("SEQ", "TYPE", "ACTOR", "DETAIL", "TIMESTAMP")
			for _, event := range events {
				table.Append([]string{
					fmt.Sprintf("%d", event.Seq),
					event.Type,
					event.Actor,
					summarizeRunEvent(event),
					formatRunTime(event.Timestamp),
				})
			}
			table.Render()
			return nil
		},
	}

	cmd.Flags().StringVar(&filters.Type, "type", "", "Filter events by type")
	cmd.Flags().IntVar(&filters.Limit, "limit", 100, "Maximum number of events to display (0 for all)")
	return cmd
}

func newRunsTimelineCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "timeline <run-id>",
		Short: "Show an operator timeline for a run",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			run, err := fetchRun(c, args[0])
			if err != nil {
				return err
			}
			events, err := fetchRunEvents(c, args[0], 0)
			if err != nil {
				return err
			}
			timeline := buildRunTimeline(*run, events)
			if isJSONOutput() {
				return printJSONValue(map[string]any{"run": run, "timeline": timeline})
			}
			if len(timeline) == 0 {
				fmt.Printf("Run %s has no timeline entries yet. Current status: %s\n", run.ID, run.Status)
				return nil
			}
			table := newTable("SEQ", "TYPE", "DETAIL", "TIMESTAMP")
			for _, entry := range timeline {
				seq := ""
				if entry.Seq > 0 {
					seq = fmt.Sprintf("%d", entry.Seq)
				}
				table.Append([]string{seq, entry.Type, entry.Summary, formatRunTime(entry.Timestamp)})
			}
			table.Render()
			return nil
		},
	}
}

func newRunsWaitCmd() *cobra.Command {
	var (
		timeout  time.Duration
		interval time.Duration
	)
	cmd := &cobra.Command{
		Use:   "wait <run-id>",
		Short: "Wait for a run to reach a terminal status",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			ctx, cancel := context.WithTimeout(context.Background(), timeout)
			defer cancel()

			var finalRun *cliRun
			err = waitForCondition(ctx, interval, func(ctx context.Context) (bool, error) {
				run, runErr := fetchRun(c, args[0])
				if runErr != nil {
					return false, runErr
				}
				finalRun = run
				return isTerminalRunStatus(run.Status), nil
			})
			if err != nil {
				if err == context.DeadlineExceeded {
					return fmt.Errorf("timed out waiting for run %q to finish", args[0])
				}
				return err
			}
			if finalRun == nil {
				return fmt.Errorf("run %q did not return a final state", args[0])
			}
			if isJSONOutput() {
				return printJSONValue(finalRun)
			}
			fmt.Printf("Run %q reached terminal status %s.\n\n", finalRun.ID, finalRun.Status)
			printRun(*finalRun)
			return nil
		},
	}
	cmd.Flags().DurationVar(&timeout, "timeout", 5*time.Minute, "Maximum time to wait for the run to finish")
	cmd.Flags().DurationVar(&interval, "interval", 2*time.Second, "Polling interval while waiting")
	return cmd
}

func newRunsExportCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "export <run-id>",
		Short: "Export a run, its events, and an operator timeline as JSON",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			run, err := fetchRun(c, args[0])
			if err != nil {
				return err
			}
			events, err := fetchRunEvents(c, args[0], 0)
			if err != nil {
				return err
			}
			export := cliRunExport{
				Run:      *run,
				Events:   events,
				Timeline: buildRunTimeline(*run, events),
			}
			if isJSONOutput() {
				return printJSONValue(export)
			}
			return printIndentedJSONValue(export)
		},
	}
}

func fetchRuns(c runAPIClient, query url.Values) ([]cliRun, error) {
	data, err := c.GetWithQuery("/runs", query)
	if err != nil {
		return nil, err
	}
	var runs []cliRun
	if err := json.Unmarshal(data, &runs); err != nil {
		return nil, fmt.Errorf("failed to parse runs response: %w", err)
	}
	return runs, nil
}

func fetchRun(c interface{ Get(string) ([]byte, error) }, id string) (*cliRun, error) {
	data, err := c.Get(fmt.Sprintf("/runs/%s", id))
	if err != nil {
		return nil, err
	}
	var run cliRun
	if err := json.Unmarshal(data, &run); err != nil {
		return nil, fmt.Errorf("failed to parse run response: %w", err)
	}
	return &run, nil
}

func fetchRunEvents(c runAPIClient, runID string, limit int) ([]cliRunEvent, error) {
	query := url.Values{}
	if limit > 0 {
		query.Set("limit", fmt.Sprintf("%d", limit))
	}
	data, err := c.GetWithQuery(fmt.Sprintf("/runs/%s/events", runID), query)
	if err != nil {
		return nil, err
	}
	var events []cliRunEvent
	if err := json.Unmarshal(data, &events); err != nil {
		return nil, fmt.Errorf("failed to parse run events response: %w", err)
	}
	return events, nil
}

func filterRuns(runs []cliRun, filters runFilters) []cliRun {
	filtered := make([]cliRun, 0, len(runs))
	for _, run := range runs {
		if filters.UserID != "" && run.UserID != filters.UserID {
			continue
		}
		if filters.ConversationID != "" && run.ConversationID != filters.ConversationID {
			continue
		}
		filtered = append(filtered, run)
	}
	sort.Slice(filtered, func(i, j int) bool {
		left := filtered[i].UpdatedAt
		if left.IsZero() {
			left = filtered[i].CreatedAt
		}
		right := filtered[j].UpdatedAt
		if right.IsZero() {
			right = filtered[j].CreatedAt
		}
		return left.After(right)
	})
	if filters.Limit > 0 && len(filtered) > filters.Limit {
		filtered = filtered[:filters.Limit]
	}
	return filtered
}

func filterRunEvents(events []cliRunEvent, filters runEventFilters) []cliRunEvent {
	filtered := make([]cliRunEvent, 0, len(events))
	for _, event := range events {
		if filters.Type != "" && !strings.EqualFold(event.Type, filters.Type) {
			continue
		}
		filtered = append(filtered, event)
	}
	sort.Slice(filtered, func(i, j int) bool {
		return filtered[i].Seq < filtered[j].Seq
	})
	if filters.Limit > 0 && len(filtered) > filters.Limit {
		filtered = filtered[len(filtered)-filters.Limit:]
	}
	return filtered
}

func buildRunTimeline(run cliRun, events []cliRunEvent) []cliRunTimelineEntry {
	if len(events) == 0 {
		timestamp := run.UpdatedAt
		if timestamp.IsZero() {
			timestamp = run.CreatedAt
		}
		return []cliRunTimelineEntry{{
			Type:      run.Status,
			Summary:   fmt.Sprintf("Run is currently %s", run.Status),
			Timestamp: timestamp,
		}}
	}
	timeline := make([]cliRunTimelineEntry, 0, len(events))
	for _, event := range events {
		timeline = append(timeline, cliRunTimelineEntry{
			Seq:       event.Seq,
			Type:      event.Type,
			Actor:     event.Actor,
			Summary:   summarizeRunEvent(event),
			Timestamp: event.Timestamp,
			Data:      event.Data,
		})
	}
	return timeline
}

func summarizeRunEvent(event cliRunEvent) string {
	if message := firstNonEmptyRunValue(dataString(event.Data, "message"), dataString(event.Data, "detail"), dataString(event.Data, "summary")); message != "" {
		return truncateRunMessage(message, 120)
	}

	switch event.Type {
	case "RUN_CREATED":
		return "Run created"
	case "USER_MESSAGE":
		return truncateRunMessage(firstNonEmptyRunValue(dataString(event.Data, "content"), dataString(event.Data, "message"), "User message received"), 120)
	case "AGENT_MESSAGE":
		return truncateRunMessage(firstNonEmptyRunValue(dataString(event.Data, "content"), dataString(event.Data, "message"), "Agent response emitted"), 120)
	case "TOOL_REQUEST", "TOOL_CALLED":
		return summarizeToolRequestEvent(event)
	case "TOOL_RESPONSE":
		tool := firstNonEmptyRunValue(dataString(event.Data, "tool_id"), dataString(event.Data, "tool"))
		statusCode := dataString(event.Data, "status_code")
		if tool != "" && statusCode != "" {
			return fmt.Sprintf("%s returned HTTP %s", tool, statusCode)
		}
		if tool != "" {
			return fmt.Sprintf("%s returned successfully", tool)
		}
		return "Tool response recorded"
	case "APPROVAL_REQUIRED":
		tool := firstNonEmptyRunValue(dataString(event.Data, "tool_id"), dataString(event.Data, "tool"), "governed tool call")
		capability := dataString(event.Data, "capability")
		if capability != "" {
			return fmt.Sprintf("Approval required for %s (%s)", tool, capability)
		}
		return fmt.Sprintf("Approval required for %s", tool)
	case "CONSENT_REQUIRED":
		tool := firstNonEmptyRunValue(dataString(event.Data, "tool_id"), dataString(event.Data, "tool"), "delegated tool call")
		return fmt.Sprintf("Consent required for %s", tool)
	case "APPROVED":
		approver := firstNonEmptyRunValue(dataString(event.Data, "approver_id"), event.Actor)
		if approver != "" {
			return fmt.Sprintf("Approved by %s", approver)
		}
		return "Approval granted"
	case "REJECTED":
		approver := firstNonEmptyRunValue(dataString(event.Data, "approver_id"), event.Actor)
		if approver != "" {
			return fmt.Sprintf("Rejected by %s", approver)
		}
		return "Approval rejected"
	case "RESUMED":
		return "Run resumed after external decision"
	case "INVOKE_REQUESTED":
		return "Agent invocation requested"
	case "INVOKE_COMPLETED":
		return "Agent invocation completed"
	case "INVOKE_FAILED":
		return firstNonEmptyRunValue(dataString(event.Data, "error"), "Agent invocation failed")
	case "COMPLETED":
		return "Run completed successfully"
	case "FAILED":
		return firstNonEmptyRunValue(dataString(event.Data, "error"), "Run failed")
	default:
		if len(event.Data) == 0 {
			return humanizeEventType(event.Type)
		}
		return truncateRunMessage(stringifyEventData(event.Data), 120)
	}
}

func summarizeToolRequestEvent(event cliRunEvent) string {
	tool := firstNonEmptyRunValue(dataString(event.Data, "tool_id"), dataString(event.Data, "tool"))
	method := dataString(event.Data, "tool_method")
	urlValue := dataString(event.Data, "tool_url")
	capability := dataString(event.Data, "capability")
	if tool == "" {
		tool = "tool"
	}
	parts := []string{tool}
	if capability != "" {
		parts = append(parts, capability)
	}
	if method != "" && urlValue != "" {
		parts = append(parts, fmt.Sprintf("%s %s", method, urlValue))
	} else if method != "" {
		parts = append(parts, method)
	} else if urlValue != "" {
		parts = append(parts, urlValue)
	}
	return fmt.Sprintf("Called %s", strings.Join(parts, " "))
}

func printRun(run cliRun) {
	fmt.Printf("ID:             %s\n", run.ID)
	fmt.Printf("Agent:          %s\n", run.AgentID)
	fmt.Printf("User:           %s\n", run.UserID)
	fmt.Printf("Status:         %s\n", run.Status)
	fmt.Printf("Namespace:      %s\n", run.Namespace)
	if run.ConversationID != "" {
		fmt.Printf("Conversation:   %s\n", run.ConversationID)
	}
	if run.BlockedActionID != "" {
		fmt.Printf("Blocked Action: %s\n", run.BlockedActionID)
	}
	if run.SurfaceTurnID != "" {
		fmt.Printf("Surface Turn:   %s\n", run.SurfaceTurnID)
	}
	if run.InvokeURL != "" {
		fmt.Printf("Invoke URL:     %s\n", run.InvokeURL)
	}
	fmt.Printf("Created:        %s\n", formatRunTime(run.CreatedAt))
	fmt.Printf("Updated:        %s\n", formatRunTime(run.UpdatedAt))
	if run.InitialMessage != "" {
		fmt.Println()
		fmt.Printf("Initial Message:\n%s\n", run.InitialMessage)
	}
}

func printJSONValue(v any) error {
	data, err := json.Marshal(v)
	if err != nil {
		return fmt.Errorf("failed to render json: %w", err)
	}
	fmt.Println(string(data))
	return nil
}

func printIndentedJSONValue(v any) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to render json: %w", err)
	}
	fmt.Println(string(data))
	return nil
}

func formatRunTime(ts time.Time) string {
	if ts.IsZero() {
		return ""
	}
	return ts.Format(time.RFC3339)
}

func isTerminalRunStatus(status string) bool {
	switch strings.ToUpper(strings.TrimSpace(status)) {
	case "COMPLETED", "FAILED":
		return true
	default:
		return false
	}
}

func dataString(data map[string]any, key string) string {
	if data == nil {
		return ""
	}
	value, ok := data[key]
	if !ok || value == nil {
		return ""
	}
	switch typed := value.(type) {
	case string:
		return typed
	case fmt.Stringer:
		return typed.String()
	default:
		return fmt.Sprintf("%v", value)
	}
}

func stringifyEventData(data map[string]any) string {
	if len(data) == 0 {
		return ""
	}
	keys := make([]string, 0, len(data))
	for key := range data {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, key := range keys {
		parts = append(parts, fmt.Sprintf("%s=%v", key, data[key]))
	}
	return strings.Join(parts, ", ")
}

func humanizeEventType(value string) string {
	value = strings.TrimSpace(strings.ReplaceAll(strings.ToLower(value), "_", " "))
	if value == "" {
		return "Event"
	}
	return strings.ToUpper(value[:1]) + value[1:]
}

func truncateRunMessage(value string, max int) string {
	value = strings.TrimSpace(value)
	if max <= 0 || len(value) <= max {
		return value
	}
	if max <= 3 {
		return value[:max]
	}
	return value[:max-3] + "..."
}

func firstNonEmptyRunValue(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}
