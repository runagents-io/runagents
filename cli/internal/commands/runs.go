package commands

import (
	"encoding/json"
	"fmt"
	"github.com/spf13/cobra"
	"net/url"
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

			query := url.Values{}
			if agentFilter != "" {
				query.Set("agent_id", agentFilter)
			}

			data, err := c.GetWithQuery("/runs", query)
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

			table := newTable("ID", "AGENT", "STATUS", "CREATED")

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

			table := newTable("SEQ", "TYPE", "MESSAGE", "TIMESTAMP")

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
