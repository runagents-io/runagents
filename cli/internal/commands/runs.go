package commands

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

func newRunsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "runs",
		Short: "Manage runs",
	}

	cmd.AddCommand(newRunsListCmd())
	cmd.AddCommand(newRunsGetCmd())
	cmd.AddCommand(newRunsEventsCmd())

	return cmd
}

func newRunsListCmd() *cobra.Command {
	var agentFilter string

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List runs",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			path := "/runs"
			if agentFilter != "" {
				path = fmt.Sprintf("/runs?agent=%s", agentFilter)
			}

			data, err := c.Get(path)
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var runs []map[string]interface{}
			if err := json.Unmarshal(data, &runs); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			table := tablewriter.NewWriter(os.Stdout)
			table.SetHeader([]string{"ID", "AGENT", "STATUS", "CREATED"})
			table.SetBorder(false)
			table.SetAutoWrapText(false)

			for _, r := range runs {
				id := stringField(r, "id")
				agent := stringField(r, "agent")
				status := stringField(r, "status")
				created := stringField(r, "created_at")
				table.Append([]string{id, agent, status, created})
			}

			table.Render()
			return nil
		},
	}

	cmd.Flags().StringVar(&agentFilter, "agent", "", "Filter runs by agent name")

	return cmd
}

func newRunsGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <id>",
		Short: "Get details of a run",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get(fmt.Sprintf("/runs/%s", id))
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var run map[string]interface{}
			if err := json.Unmarshal(data, &run); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			fmt.Printf("ID:      %s\n", stringField(run, "id"))
			fmt.Printf("Agent:   %s\n", stringField(run, "agent"))
			fmt.Printf("Status:  %s\n", stringField(run, "status"))
			fmt.Printf("Created: %s\n", stringField(run, "created_at"))

			if actions, ok := run["blocked_actions"]; ok {
				fmt.Printf("Blocked: %v\n", actions)
			}

			return nil
		},
	}
}

func newRunsEventsCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "events <id>",
		Short: "Show events for a run",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]

			c, err := newAPIClient()
			if err != nil {
				return err
			}

			data, err := c.Get(fmt.Sprintf("/runs/%s/events", id))
			if err != nil {
				return err
			}

			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var events []map[string]interface{}
			if err := json.Unmarshal(data, &events); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}

			if len(events) == 0 {
				fmt.Println("No events found.")
				return nil
			}

			table := tablewriter.NewWriter(os.Stdout)
			table.SetHeader([]string{"SEQ", "TYPE", "MESSAGE", "TIMESTAMP"})
			table.SetBorder(false)
			table.SetAutoWrapText(false)

			for _, e := range events {
				seq := stringField(e, "sequence")
				eventType := stringField(e, "type")
				message := stringField(e, "message")
				timestamp := stringField(e, "timestamp")
				table.Append([]string{seq, eventType, message, timestamp})
			}

			table.Render()
			return nil
		},
	}
}
