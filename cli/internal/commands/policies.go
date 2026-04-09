package commands

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
)

type cliPolicyResponse struct {
	Name      string           `json:"name"`
	Namespace string           `json:"namespace"`
	Spec      cliPolicySpec    `json:"spec"`
	Status    cliPolicyStatus  `json:"status"`
	UsedBy    []cliPolicyUsage `json:"used_by,omitempty"`
}

type cliPolicyStatus struct {
	Ready   bool   `json:"ready"`
	Message string `json:"message,omitempty"`
}

type cliPolicyUsage struct {
	Name      string `json:"name"`
	Namespace string `json:"namespace"`
}

type cliPolicySpec struct {
	Policies  []cliPolicyRule   `json:"policies"`
	Approvals []cliApprovalRule `json:"approvals,omitempty"`
}

type cliPolicyRule struct {
	Permission string   `json:"permission"`
	Operations []string `json:"operations,omitempty"`
	Resource   string   `json:"resource,omitempty"`
	Tags       []string `json:"tags,omitempty"`
}

type cliApprovalRule struct {
	Name            string               `json:"name,omitempty"`
	ToolIDs         []string             `json:"toolIds,omitempty"`
	Capabilities    []string             `json:"capabilities,omitempty"`
	Operations      []string             `json:"operations,omitempty"`
	Resource        string               `json:"resource,omitempty"`
	Tags            []string             `json:"tags,omitempty"`
	Approvers       cliApprovalApprovers `json:"approvers"`
	DefaultDuration string               `json:"defaultDuration,omitempty"`
	Delivery        *cliApprovalDelivery `json:"delivery,omitempty"`
}

type cliApprovalApprovers struct {
	Groups []string `json:"groups"`
	Match  string   `json:"match,omitempty"`
}

type cliApprovalDelivery struct {
	Connectors   []string `json:"connectors,omitempty"`
	Mode         string   `json:"mode,omitempty"`
	FallbackToUI bool     `json:"fallbackToUI,omitempty"`
}

type cliPolicyApplyRequest struct {
	Name string        `json:"name"`
	Spec cliPolicySpec `json:"spec"`
}

type cliTranslatePolicyResponse struct {
	Rules []cliPolicyRule `json:"rules"`
}

func newPoliciesCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "policies",
		Short: "Manage policy rules and approval routing",
	}

	cmd.AddCommand(newPoliciesListCmd())
	cmd.AddCommand(newPoliciesGetCmd())
	cmd.AddCommand(newPoliciesApplyCmd())
	cmd.AddCommand(newPoliciesDeleteCmd())
	cmd.AddCommand(newPoliciesTranslateCmd())

	return cmd
}

func newPoliciesListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List policies in the current workspace",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get("/api/policies")
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			var resp []cliPolicyResponse
			if err := json.Unmarshal(data, &resp); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			if len(resp) == 0 {
				fmt.Println("No policies found.")
				return nil
			}
			table := newTable("NAME", "READY", "RULES", "APPROVALS", "USED BY")
			for _, policy := range resp {
				table.Append([]string{
					policy.Name,
					boolWord(policy.Status.Ready),
					fmt.Sprintf("%d", len(policy.Spec.Policies)),
					fmt.Sprintf("%d", len(policy.Spec.Approvals)),
					fmt.Sprintf("%d", len(policy.UsedBy)),
				})
			}
			table.Render()
			return nil
		},
	}
}

func newPoliciesGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <name>",
		Short: "Get a policy and its usage details",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get(fmt.Sprintf("/api/policies/%s", args[0]))
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var policy cliPolicyResponse
			if err := json.Unmarshal(data, &policy); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			printPolicy(policy)
			return nil
		},
	}
}

func newPoliciesApplyCmd() *cobra.Command {
	var (
		filePath string
		name     string
	)
	cmd := &cobra.Command{
		Use:   "apply -f <file>",
		Short: "Create or update a policy from YAML or JSON",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(filePath) == "" {
				return fmt.Errorf("--file is required")
			}
			req, err := loadPolicyApplyRequest(filePath, name)
			if err != nil {
				return err
			}
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			method := "created"
			path := "/api/policies"
			if _, err := c.Get(fmt.Sprintf("/api/policies/%s", req.Name)); err == nil {
				method = "updated"
				path = fmt.Sprintf("/api/policies/%s", req.Name)
				data, putErr := c.Put(path, req)
				if putErr != nil {
					return putErr
				}
				return printAppliedPolicy(req.Name, method, data)
			} else if extractHTTPStatus(err) != httpStatusNotFound {
				return err
			}

			data, err := c.Post(path, req)
			if err != nil {
				return err
			}
			return printAppliedPolicy(req.Name, method, data)
		},
	}
	cmd.Flags().StringVarP(&filePath, "file", "f", "", "Policy YAML or JSON file")
	cmd.Flags().StringVar(&name, "name", "", "Override the policy name (required when the file contains only a raw spec)")
	return cmd
}

func newPoliciesDeleteCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "delete <name>",
		Short: "Delete a policy",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			if err := c.Delete(fmt.Sprintf("/api/policies/%s", args[0])); err != nil {
				return err
			}
			fmt.Printf("Policy %q deleted.\n", args[0])
			return nil
		},
	}
}

func newPoliciesTranslateCmd() *cobra.Command {
	var text string
	cmd := &cobra.Command{
		Use:   "translate --from <text>",
		Short: "Translate natural language into policy rules",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(text) == "" {
				return fmt.Errorf("--from is required")
			}
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Post("/api/policies/translate", map[string]string{"text": text})
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}
			var resp cliTranslatePolicyResponse
			if err := json.Unmarshal(data, &resp); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			if len(resp.Rules) == 0 {
				fmt.Println("No rules generated.")
				return nil
			}
			table := newTable("PERMISSION", "OPERATIONS", "RESOURCE", "TAGS")
			for _, rule := range resp.Rules {
				table.Append([]string{
					rule.Permission,
					strings.Join(rule.Operations, ", "),
					rule.Resource,
					strings.Join(rule.Tags, ", "),
				})
			}
			table.Render()
			return nil
		},
	}
	cmd.Flags().StringVar(&text, "from", "", "Natural-language policy description")
	return cmd
}

const httpStatusNotFound = 404

func boolWord(v bool) string {
	if v {
		return "yes"
	}
	return "no"
}

func printPolicy(policy cliPolicyResponse) {
	fmt.Printf("Name:       %s\n", policy.Name)
	fmt.Printf("Namespace:  %s\n", policy.Namespace)
	fmt.Printf("Ready:      %s\n", boolWord(policy.Status.Ready))
	if policy.Status.Message != "" {
		fmt.Printf("Status:     %s\n", policy.Status.Message)
	}
	if len(policy.UsedBy) > 0 {
		usedBy := make([]string, 0, len(policy.UsedBy))
		for _, usage := range policy.UsedBy {
			usedBy = append(usedBy, usage.Name)
		}
		fmt.Printf("Used by:    %s\n", strings.Join(usedBy, ", "))
	}

	fmt.Println()
	fmt.Println("Policy rules:")
	for i, rule := range policy.Spec.Policies {
		fmt.Printf("  %d. %s", i+1, rule.Permission)
		if len(rule.Operations) > 0 {
			fmt.Printf(" %s", strings.Join(rule.Operations, ","))
		}
		if rule.Resource != "" {
			fmt.Printf(" %s", rule.Resource)
		}
		if len(rule.Tags) > 0 {
			fmt.Printf(" [tags: %s]", strings.Join(rule.Tags, ", "))
		}
		fmt.Println()
	}
	if len(policy.Spec.Approvals) == 0 {
		return
	}
	fmt.Println()
	fmt.Println("Approval routes:")
	for i, approval := range policy.Spec.Approvals {
		label := approval.Name
		if label == "" {
			label = fmt.Sprintf("approval-%d", i+1)
		}
		fmt.Printf("  %d. %s -> groups: %s\n", i+1, label, strings.Join(approval.Approvers.Groups, ", "))
	}
}

func printAppliedPolicy(name, action string, data []byte) error {
	if isJSONOutput() {
		fmt.Println(string(data))
		return nil
	}
	var policy cliPolicyResponse
	if err := json.Unmarshal(data, &policy); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}
	fmt.Printf("Policy %q %s.\n", name, action)
	fmt.Printf("Rules: %d, approvals: %d\n", len(policy.Spec.Policies), len(policy.Spec.Approvals))
	return nil
}

func loadPolicyApplyRequest(path, overrideName string) (cliPolicyApplyRequest, error) {
	var raw map[string]any
	if err := decodeStructuredFile(path, &raw); err != nil {
		return cliPolicyApplyRequest{}, err
	}

	var req cliPolicyApplyRequest
	if _, ok := raw["spec"]; ok {
		data, err := json.Marshal(raw)
		if err != nil {
			return cliPolicyApplyRequest{}, fmt.Errorf("marshal policy request: %w", err)
		}
		if err := json.Unmarshal(data, &req); err != nil {
			return cliPolicyApplyRequest{}, fmt.Errorf("decode policy request: %w", err)
		}
	} else {
		data, err := json.Marshal(raw)
		if err != nil {
			return cliPolicyApplyRequest{}, fmt.Errorf("marshal policy spec: %w", err)
		}
		if err := json.Unmarshal(data, &req.Spec); err != nil {
			return cliPolicyApplyRequest{}, fmt.Errorf("decode policy spec: %w", err)
		}
	}

	if strings.TrimSpace(overrideName) != "" {
		req.Name = strings.TrimSpace(overrideName)
	}
	if strings.TrimSpace(req.Name) == "" {
		return cliPolicyApplyRequest{}, fmt.Errorf("policy name is required; add it to the file or pass --name")
	}
	if len(req.Spec.Policies) == 0 {
		return cliPolicyApplyRequest{}, fmt.Errorf("policy spec must include at least one rule")
	}
	return req, nil
}
