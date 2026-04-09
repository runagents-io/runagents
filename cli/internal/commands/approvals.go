package commands

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
)

type approvalDecisionBody struct {
	Scope    string `json:"scope,omitempty"`
	Duration string `json:"duration,omitempty"`
}

func newApprovalsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "approvals",
		Short: "Manage access request approvals",
	}

	cmd.AddCommand(newApprovalsListCmd())
	cmd.AddCommand(newApprovalsApproveCmd())
	cmd.AddCommand(newApprovalsRejectCmd())

	return cmd
}

func newApprovalsListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List access requests",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get("/governance/requests")
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var requests []map[string]interface{}
			if err := json.Unmarshal(data, &requests); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			if len(requests) == 0 {
				fmt.Println("No access requests found.")
				return nil
			}

			table := newTable("ID", "AGENT", "TOOL", "STATUS", "CREATED")

			for _, r := range requests {
				id := stringField(r, "id")
				agent := stringField(r, "agent")
				tool := stringField(r, "tool")
				status := stringField(r, "status")
				created := stringField(r, "created_at")
				table.Append([]string{id, agent, tool, status, created})
			}

			table.Render()
			return nil
		},
	}
}

func newApprovalsApproveCmd() *cobra.Command {
	var (
		scope    string
		duration string
	)
	cmd := &cobra.Command{
		Use:   "approve <id>",
		Short: "Approve an access request",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			body, err := buildApprovalDecision(scope, duration)
			if err != nil {
				return err
			}

			_, err = c.Post(fmt.Sprintf("/governance/requests/%s/approve", id), body)
			if err != nil {
				return err
			}

			if body == nil {
				fmt.Printf("Access request %q approved.\n", id)
				return nil
			}

			switch body.Scope {
			case "once":
				fmt.Printf("Access request %q approved for one action.\n", id)
			case "run":
				fmt.Printf("Access request %q approved for the current run.\n", id)
			case "agent_user_ttl":
				if body.Duration != "" {
					fmt.Printf("Access request %q approved for %s.\n", id, body.Duration)
				} else {
					fmt.Printf("Access request %q approved for a time window.\n", id)
				}
			default:
				fmt.Printf("Access request %q approved.\n", id)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&scope, "scope", "", "Approval scope: once, run, or window")
	cmd.Flags().StringVar(&duration, "duration", "", "Approval duration for window scope (for example 1h or 4h)")
	return cmd
}

func buildApprovalDecision(scope, duration string) (*approvalDecisionBody, error) {
	normalizedScope, err := normalizeApprovalScope(scope, duration)
	if err != nil {
		return nil, err
	}
	duration = strings.TrimSpace(duration)
	if normalizedScope == "" && duration == "" {
		return nil, nil
	}
	return &approvalDecisionBody{
		Scope:    normalizedScope,
		Duration: duration,
	}, nil
}

func normalizeApprovalScope(scope, duration string) (string, error) {
	scope = strings.ToLower(strings.TrimSpace(scope))
	duration = strings.TrimSpace(duration)

	if scope == "" {
		if duration != "" {
			return "agent_user_ttl", nil
		}
		return "", nil
	}

	switch scope {
	case "once":
		if duration != "" {
			return "", fmt.Errorf("--duration can only be used with --scope window")
		}
		return "once", nil
	case "run":
		if duration != "" {
			return "", fmt.Errorf("--duration can only be used with --scope window")
		}
		return "run", nil
	case "window", "ttl", "agent_user_ttl":
		return "agent_user_ttl", nil
	default:
		return "", fmt.Errorf("invalid approval scope %q (expected once, run, or window)", scope)
	}
}

func newApprovalsRejectCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "reject <id>",
		Short: "Reject an access request",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			_, err = c.Post(fmt.Sprintf("/governance/requests/%s/reject", id), nil)
			if err != nil {
				return err
			}

			fmt.Printf("Access request %q rejected.\n", id)
			return nil
		},
	}
}
