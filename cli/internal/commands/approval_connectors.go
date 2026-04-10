package commands

import (
	"encoding/json"
	"fmt"
	"net/url"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

type cliApprovalConnector struct {
	ID                string            `json:"id"`
	Name              string            `json:"name"`
	Type              string            `json:"type"`
	Endpoint          string            `json:"endpoint"`
	Headers           map[string]string `json:"headers,omitempty"`
	Enabled           bool              `json:"enabled"`
	TimeoutSeconds    int               `json:"timeout_seconds"`
	SlackSecurityMode string            `json:"slack_security_mode,omitempty"`
	CreatedAt         time.Time         `json:"created_at"`
	UpdatedAt         time.Time         `json:"updated_at"`
}

type cliApprovalConnectorApplyRequest struct {
	ID                string            `json:"id,omitempty" yaml:"id,omitempty"`
	Name              string            `json:"name,omitempty" yaml:"name,omitempty"`
	Type              string            `json:"type,omitempty" yaml:"type,omitempty"`
	Endpoint          string            `json:"endpoint,omitempty" yaml:"endpoint,omitempty"`
	Headers           map[string]string `json:"headers,omitempty" yaml:"headers,omitempty"`
	Enabled           *bool             `json:"enabled,omitempty" yaml:"enabled,omitempty"`
	TimeoutSeconds    *int              `json:"timeout_seconds,omitempty" yaml:"timeout_seconds,omitempty"`
	SlackSecurityMode string            `json:"slack_security_mode,omitempty" yaml:"slack_security_mode,omitempty"`
}

type cliApprovalConnectorCreateRequest struct {
	Name           string            `json:"name"`
	Type           string            `json:"type,omitempty"`
	Endpoint       string            `json:"endpoint"`
	Headers        map[string]string `json:"headers,omitempty"`
	Enabled        *bool             `json:"enabled,omitempty"`
	TimeoutSeconds *int              `json:"timeout_seconds,omitempty"`
	SlackSecurity  string            `json:"slack_security_mode,omitempty"`
}

type cliApprovalConnectorUpdateRequest struct {
	Name           *string            `json:"name,omitempty"`
	Type           *string            `json:"type,omitempty"`
	Endpoint       *string            `json:"endpoint,omitempty"`
	Headers        *map[string]string `json:"headers,omitempty"`
	Enabled        *bool              `json:"enabled,omitempty"`
	TimeoutSeconds *int               `json:"timeout_seconds,omitempty"`
	SlackSecurity  *string            `json:"slack_security_mode,omitempty"`
}

type cliApprovalConnectorTestRequest struct {
	Type           string            `json:"type,omitempty"`
	Endpoint       string            `json:"endpoint"`
	Headers        map[string]string `json:"headers,omitempty"`
	TimeoutSeconds *int              `json:"timeout_seconds,omitempty"`
	SlackSecurity  string            `json:"slack_security_mode,omitempty"`
}

type cliApprovalConnectorTestCheck struct {
	ID         string `json:"id"`
	Label      string `json:"label"`
	Status     string `json:"status"`
	Message    string `json:"message"`
	DurationMs int64  `json:"duration_ms,omitempty"`
}

type cliApprovalConnectorTestResponse struct {
	Status        string                          `json:"status"`
	ConnectorType string                          `json:"connector_type"`
	Endpoint      string                          `json:"endpoint"`
	Checks        []cliApprovalConnectorTestCheck `json:"checks"`
}

type cliApprovalConnectorDefaultsResponse struct {
	DefaultDeliveryMode  string `json:"default_delivery_mode"`
	DefaultFallbackToUI  bool   `json:"default_fallback_to_ui"`
	DefaultTimeoutSecond int    `json:"default_timeout_seconds"`
	MinTimeoutSecond     int    `json:"min_timeout_seconds"`
	MaxTimeoutSecond     int    `json:"max_timeout_seconds"`
}

type cliApprovalConnectorDefaultsUpdate struct {
	DefaultDeliveryMode  *string `json:"default_delivery_mode,omitempty"`
	DefaultFallbackToUI  *bool   `json:"default_fallback_to_ui,omitempty"`
	DefaultTimeoutSecond *int    `json:"default_timeout_seconds,omitempty"`
}

type cliApprovalConnectorActivity struct {
	ID            string    `json:"id"`
	Timestamp     time.Time `json:"timestamp"`
	Event         string    `json:"event"`
	ConnectorID   string    `json:"connector_id,omitempty"`
	ConnectorName string    `json:"connector_name,omitempty"`
	RequestID     string    `json:"request_id,omitempty"`
	ActionID      string    `json:"action_id,omitempty"`
	RunID         string    `json:"run_id,omitempty"`
	Decision      string    `json:"decision,omitempty"`
	ApproverID    string    `json:"approver_id,omitempty"`
	StatusCode    int       `json:"status_code,omitempty"`
	DurationMs    int64     `json:"duration_ms,omitempty"`
	Message       string    `json:"message,omitempty"`
}

func newApprovalConnectorsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "approval-connectors",
		Short: "Manage approval delivery connectors and defaults",
	}

	cmd.AddCommand(newApprovalConnectorsListCmd())
	cmd.AddCommand(newApprovalConnectorsGetCmd())
	cmd.AddCommand(newApprovalConnectorsApplyCmd())
	cmd.AddCommand(newApprovalConnectorsDeleteCmd())
	cmd.AddCommand(newApprovalConnectorsTestCmd())
	cmd.AddCommand(newApprovalConnectorsDefaultsCmd())
	cmd.AddCommand(newApprovalConnectorsActivityCmd())

	return cmd
}

func newApprovalConnectorsListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List approval connectors in the current workspace",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get("/api/settings/approval-connectors")
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			var connectors []cliApprovalConnector
			if err := json.Unmarshal(data, &connectors); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			if len(connectors) == 0 {
				fmt.Println("No approval connectors found.")
				return nil
			}
			table := newTable("ID", "NAME", "TYPE", "ENABLED", "TIMEOUT", "ENDPOINT")
			for _, connector := range connectors {
				table.Append([]string{
					connector.ID,
					connector.Name,
					connector.Type,
					boolWord(connector.Enabled),
					fmt.Sprintf("%ds", connector.TimeoutSeconds),
					connector.Endpoint,
				})
			}
			table.Render()
			return nil
		},
	}
}

func newApprovalConnectorsGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <id>",
		Short: "Get a single approval connector",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get("/api/settings/approval-connectors/" + strings.TrimSpace(args[0]))
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			var connector cliApprovalConnector
			if err := json.Unmarshal(data, &connector); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			printApprovalConnector(connector)
			return nil
		},
	}
}

func newApprovalConnectorsApplyCmd() *cobra.Command {
	var filePath string
	cmd := &cobra.Command{
		Use:   "apply -f <file>",
		Short: "Create or update an approval connector from YAML or JSON",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(filePath) == "" {
				return fmt.Errorf("--file is required")
			}
			req, err := loadApprovalConnectorApplyRequest(filePath)
			if err != nil {
				return err
			}
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			connectors, err := fetchApprovalConnectors(c)
			if err != nil {
				return err
			}
			target, err := resolveApprovalConnectorTarget(connectors, req)
			if err != nil {
				return err
			}
			action := "created"
			var data []byte
			if target != nil {
				action = "updated"
				patch := buildApprovalConnectorPatch(req)
				data, err = c.Patch("/api/settings/approval-connectors/"+target.ID, patch)
			} else {
				createReq, createErr := buildApprovalConnectorCreate(req)
				if createErr != nil {
					return createErr
				}
				data, err = c.Post("/api/settings/approval-connectors", createReq)
			}
			if err != nil {
				return err
			}
			return printAppliedApprovalConnector(req, action, data)
		},
	}
	cmd.Flags().StringVarP(&filePath, "file", "f", "", "Connector YAML or JSON file")
	return cmd
}

func newApprovalConnectorsDeleteCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "delete <id>",
		Short: "Delete an approval connector",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			id := strings.TrimSpace(args[0])
			if id == "" {
				return fmt.Errorf("connector id is required")
			}
			if err := c.Delete("/api/settings/approval-connectors/" + id); err != nil {
				return err
			}
			fmt.Printf("Approval connector %q deleted.\n", id)
			return nil
		},
	}
}

func newApprovalConnectorsTestCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "test <id>",
		Short: "Test an approval connector by replaying its current configuration",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			id := strings.TrimSpace(args[0])
			data, err := c.Get("/api/settings/approval-connectors/" + id)
			if err != nil {
				return err
			}
			var connector cliApprovalConnector
			if err := json.Unmarshal(data, &connector); err != nil {
				return fmt.Errorf("failed to parse connector response: %w", err)
			}
			testReq := buildApprovalConnectorTestRequest(connector)
			result, err := c.Post("/api/settings/approval-connectors/test", testReq)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(result))
				return nil
			}
			var resp cliApprovalConnectorTestResponse
			if err := json.Unmarshal(result, &resp); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			printApprovalConnectorTestResult(connector, resp)
			return nil
		},
	}
}

func newApprovalConnectorsDefaultsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "defaults",
		Short: "View or update default approval connector delivery settings",
	}
	cmd.AddCommand(newApprovalConnectorsDefaultsGetCmd())
	cmd.AddCommand(newApprovalConnectorsDefaultsSetCmd())
	return cmd
}

func newApprovalConnectorsDefaultsGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get",
		Short: "Show default approval connector settings",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get("/api/settings/approval-connectors/defaults")
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			var defaults cliApprovalConnectorDefaultsResponse
			if err := json.Unmarshal(data, &defaults); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			printApprovalConnectorDefaults(defaults)
			return nil
		},
	}
}

func newApprovalConnectorsDefaultsSetCmd() *cobra.Command {
	var (
		deliveryMode string
		fallbackToUI bool
		timeout      int
	)
	cmd := &cobra.Command{
		Use:   "set",
		Short: "Update default approval connector settings",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			body := cliApprovalConnectorDefaultsUpdate{}
			changed := false
			if cmd.Flags().Changed("delivery-mode") {
				trimmed := strings.TrimSpace(deliveryMode)
				body.DefaultDeliveryMode = &trimmed
				changed = true
			}
			if cmd.Flags().Changed("fallback-to-ui") {
				body.DefaultFallbackToUI = &fallbackToUI
				changed = true
			}
			if cmd.Flags().Changed("timeout-seconds") {
				body.DefaultTimeoutSecond = &timeout
				changed = true
			}
			if !changed {
				return fmt.Errorf("set at least one flag: --delivery-mode, --fallback-to-ui, or --timeout-seconds")
			}
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Put("/api/settings/approval-connectors/defaults", body)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			var defaults cliApprovalConnectorDefaultsResponse
			if err := json.Unmarshal(data, &defaults); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			fmt.Println("Approval connector defaults updated.")
			fmt.Println()
			printApprovalConnectorDefaults(defaults)
			return nil
		},
	}
	cmd.Flags().StringVar(&deliveryMode, "delivery-mode", "", "Default connector delivery mode (for example first_success or all)")
	cmd.Flags().BoolVar(&fallbackToUI, "fallback-to-ui", false, "Whether to fall back to the console when connector delivery does not succeed")
	cmd.Flags().IntVar(&timeout, "timeout-seconds", 0, "Default connector timeout in seconds")
	return cmd
}

func newApprovalConnectorsActivityCmd() *cobra.Command {
	var limit int
	cmd := &cobra.Command{
		Use:   "activity",
		Short: "Show recent approval connector activity",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			query := approvalConnectorActivityQuery(limit)
			data, err := c.GetWithQuery("/api/settings/approval-connectors/activity", query)
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			var events []cliApprovalConnectorActivity
			if err := json.Unmarshal(data, &events); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			if len(events) == 0 {
				fmt.Println("No approval connector activity found.")
				return nil
			}
			table := newTable("TIMESTAMP", "EVENT", "CONNECTOR", "REQUEST", "RESULT", "MESSAGE")
			for _, event := range events {
				table.Append([]string{
					formatApprovalConnectorTime(event.Timestamp),
					event.Event,
					approvalConnectorDisplayName(event.ConnectorName, event.ConnectorID),
					firstNonEmptyConnectorValue(event.RequestID, event.ActionID, event.RunID),
					approvalConnectorActivityResult(event),
					event.Message,
				})
			}
			table.Render()
			return nil
		},
	}
	cmd.Flags().IntVar(&limit, "limit", 50, "Maximum number of activity events to return")
	return cmd
}

func fetchApprovalConnectors(c interface{ Get(string) ([]byte, error) }) ([]cliApprovalConnector, error) {
	data, err := c.Get("/api/settings/approval-connectors")
	if err != nil {
		return nil, err
	}
	var connectors []cliApprovalConnector
	if err := json.Unmarshal(data, &connectors); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}
	return connectors, nil
}

func loadApprovalConnectorApplyRequest(path string) (cliApprovalConnectorApplyRequest, error) {
	var req cliApprovalConnectorApplyRequest
	if err := decodeStructuredFile(path, &req); err != nil {
		return cliApprovalConnectorApplyRequest{}, err
	}
	req.ID = strings.TrimSpace(req.ID)
	req.Name = strings.TrimSpace(req.Name)
	req.Type = strings.TrimSpace(req.Type)
	req.Endpoint = strings.TrimSpace(req.Endpoint)
	req.SlackSecurityMode = strings.TrimSpace(req.SlackSecurityMode)
	if req.ID == "" && req.Name == "" {
		return cliApprovalConnectorApplyRequest{}, fmt.Errorf("connector file must include either id or name")
	}
	return req, nil
}

func resolveApprovalConnectorTarget(connectors []cliApprovalConnector, req cliApprovalConnectorApplyRequest) (*cliApprovalConnector, error) {
	if req.ID != "" {
		for i := range connectors {
			if connectors[i].ID == req.ID {
				return &connectors[i], nil
			}
		}
	}
	if req.Name == "" {
		return nil, nil
	}
	matches := make([]cliApprovalConnector, 0, 1)
	for _, connector := range connectors {
		if connector.Name == req.Name {
			matches = append(matches, connector)
		}
	}
	if len(matches) == 0 {
		return nil, nil
	}
	if len(matches) > 1 {
		return nil, fmt.Errorf("multiple approval connectors share the name %q; use an id in the file instead", req.Name)
	}
	return &matches[0], nil
}

func buildApprovalConnectorCreate(req cliApprovalConnectorApplyRequest) (cliApprovalConnectorCreateRequest, error) {
	if req.Name == "" {
		return cliApprovalConnectorCreateRequest{}, fmt.Errorf("connector name is required when creating a connector")
	}
	if req.Endpoint == "" {
		return cliApprovalConnectorCreateRequest{}, fmt.Errorf("connector endpoint is required when creating a connector")
	}
	return cliApprovalConnectorCreateRequest{
		Name:           req.Name,
		Type:           req.Type,
		Endpoint:       req.Endpoint,
		Headers:        req.Headers,
		Enabled:        req.Enabled,
		TimeoutSeconds: req.TimeoutSeconds,
		SlackSecurity:  req.SlackSecurityMode,
	}, nil
}

func buildApprovalConnectorPatch(req cliApprovalConnectorApplyRequest) cliApprovalConnectorUpdateRequest {
	patch := cliApprovalConnectorUpdateRequest{
		Enabled:        req.Enabled,
		TimeoutSeconds: req.TimeoutSeconds,
	}
	if req.Name != "" {
		name := req.Name
		patch.Name = &name
	}
	if req.Type != "" {
		connectorType := req.Type
		patch.Type = &connectorType
	}
	if req.Endpoint != "" {
		endpoint := req.Endpoint
		patch.Endpoint = &endpoint
	}
	if req.Headers != nil {
		headers := req.Headers
		patch.Headers = &headers
	}
	if req.SlackSecurityMode != "" {
		security := req.SlackSecurityMode
		patch.SlackSecurity = &security
	}
	return patch
}

func buildApprovalConnectorTestRequest(connector cliApprovalConnector) cliApprovalConnectorTestRequest {
	return cliApprovalConnectorTestRequest{
		Type:           connector.Type,
		Endpoint:       connector.Endpoint,
		Headers:        connector.Headers,
		TimeoutSeconds: approvalConnectorOptionalInt(connector.TimeoutSeconds),
		SlackSecurity:  connector.SlackSecurityMode,
	}
}

func approvalConnectorOptionalInt(v int) *int {
	if v == 0 {
		return nil
	}
	value := v
	return &value
}

func approvalConnectorActivityQuery(limit int) url.Values {
	if limit <= 0 {
		return nil
	}
	return url.Values{"limit": {strconv.Itoa(limit)}}
}

func printApprovalConnector(connector cliApprovalConnector) {
	fmt.Printf("ID:         %s\n", connector.ID)
	fmt.Printf("Name:       %s\n", connector.Name)
	fmt.Printf("Type:       %s\n", connector.Type)
	fmt.Printf("Endpoint:   %s\n", connector.Endpoint)
	fmt.Printf("Enabled:    %s\n", boolWord(connector.Enabled))
	fmt.Printf("Timeout:    %ds\n", connector.TimeoutSeconds)
	if connector.SlackSecurityMode != "" {
		fmt.Printf("Security:   %s\n", connector.SlackSecurityMode)
	}
	if !connector.CreatedAt.IsZero() {
		fmt.Printf("Created:    %s\n", connector.CreatedAt.Format(time.RFC3339))
	}
	if !connector.UpdatedAt.IsZero() {
		fmt.Printf("Updated:    %s\n", connector.UpdatedAt.Format(time.RFC3339))
	}
	if len(connector.Headers) == 0 {
		return
	}
	fmt.Println()
	fmt.Println("Headers:")
	keys := make([]string, 0, len(connector.Headers))
	for key := range connector.Headers {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		fmt.Printf("  %s: %s\n", key, connector.Headers[key])
	}
}

func printAppliedApprovalConnector(req cliApprovalConnectorApplyRequest, action string, data []byte) error {
	if isJSONOutput() {
		fmt.Println(string(data))
		return nil
	}
	var connector cliApprovalConnector
	if err := json.Unmarshal(data, &connector); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}
	name := req.Name
	if name == "" {
		name = connector.Name
	}
	fmt.Printf("Approval connector %q %s.\n", name, action)
	fmt.Printf("ID: %s, type: %s, enabled: %s\n", connector.ID, connector.Type, boolWord(connector.Enabled))
	return nil
}

func printApprovalConnectorTestResult(connector cliApprovalConnector, resp cliApprovalConnectorTestResponse) {
	fmt.Printf("Connector:  %s\n", connector.Name)
	fmt.Printf("Type:       %s\n", resp.ConnectorType)
	fmt.Printf("Endpoint:   %s\n", resp.Endpoint)
	fmt.Printf("Status:     %s\n", resp.Status)
	fmt.Println()
	table := newTable("CHECK", "STATUS", "DURATION", "MESSAGE")
	for _, check := range resp.Checks {
		duration := ""
		if check.DurationMs > 0 {
			duration = fmt.Sprintf("%dms", check.DurationMs)
		}
		table.Append([]string{check.Label, check.Status, duration, check.Message})
	}
	table.Render()
}

func printApprovalConnectorDefaults(defaults cliApprovalConnectorDefaultsResponse) {
	fmt.Printf("Delivery mode:   %s\n", defaults.DefaultDeliveryMode)
	fmt.Printf("Fallback to UI:  %s\n", boolWord(defaults.DefaultFallbackToUI))
	fmt.Printf("Timeout:         %ds\n", defaults.DefaultTimeoutSecond)
	fmt.Printf("Allowed timeout: %ds-%ds\n", defaults.MinTimeoutSecond, defaults.MaxTimeoutSecond)
}

func approvalConnectorDisplayName(name, id string) string {
	if strings.TrimSpace(name) != "" {
		return name
	}
	return id
}

func approvalConnectorActivityResult(event cliApprovalConnectorActivity) string {
	if event.Decision != "" {
		return event.Decision
	}
	if event.StatusCode != 0 {
		return strconv.Itoa(event.StatusCode)
	}
	return ""
}

func formatApprovalConnectorTime(ts time.Time) string {
	if ts.IsZero() {
		return ""
	}
	return ts.Format(time.RFC3339)
}

func firstNonEmptyConnectorValue(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}
