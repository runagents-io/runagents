package commands

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

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

			table := tablewriter.NewWriter(os.Stdout)
			table.SetHeader([]string{"ID", "AGENT", "TOOL", "STATUS", "CREATED"})
			table.SetBorder(false)
			table.SetAutoWrapText(false)

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
	return &cobra.Command{
		Use:   "approve <id>",
		Short: "Approve an access request",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			_, err = c.Post(fmt.Sprintf("/governance/requests/%s/approve", id), nil)
			if err != nil {
				return err
			}

			fmt.Printf("Access request %q approved.\n", id)
			return nil
		},
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
