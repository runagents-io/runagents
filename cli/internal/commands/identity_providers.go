package commands

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
)

type cliIdentityProviderResponse struct {
	Name      string                  `json:"name"`
	Namespace string                  `json:"namespace"`
	Spec      cliIdentityProviderSpec `json:"spec"`
}

type cliIdentityProviderSpec struct {
	Host             string                    `json:"host" yaml:"host"`
	IdentityProvider cliIdentityProviderConfig `json:"identityProvider" yaml:"identityProvider"`
	UserIDClaim      string                    `json:"userIDClaim" yaml:"userIDClaim"`
	AllowedDomains   []string                  `json:"allowedDomains,omitempty" yaml:"allowedDomains,omitempty"`
}

type cliIdentityProviderConfig struct {
	Issuer    string   `json:"issuer" yaml:"issuer"`
	JWKSURI   string   `json:"jwksUri" yaml:"jwksUri"`
	Audiences []string `json:"audiences,omitempty" yaml:"audiences,omitempty"`
}

type cliIdentityProviderApplyRequest struct {
	Name      string                  `json:"name,omitempty" yaml:"name,omitempty"`
	Namespace string                  `json:"namespace,omitempty" yaml:"namespace,omitempty"`
	Spec      cliIdentityProviderSpec `json:"spec,omitempty" yaml:"spec,omitempty"`
}

func newIdentityProvidersCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "identity-providers",
		Short: "Manage end-user identity providers",
	}

	cmd.AddCommand(newIdentityProvidersListCmd())
	cmd.AddCommand(newIdentityProvidersGetCmd())
	cmd.AddCommand(newIdentityProvidersApplyCmd())
	cmd.AddCommand(newIdentityProvidersDeleteCmd())

	return cmd
}

func newIdentityProvidersListCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: "List identity providers in the current workspace",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get("/api/identity-providers")
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var providers []cliIdentityProviderResponse
			if err := json.Unmarshal(data, &providers); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			if len(providers) == 0 {
				fmt.Println("No identity providers found.")
				return nil
			}

			table := newTable("NAME", "HOST", "USER CLAIM", "ISSUER", "DOMAINS")
			for _, provider := range providers {
				table.Append([]string{
					provider.Name,
					provider.Spec.Host,
					provider.Spec.UserIDClaim,
					provider.Spec.IdentityProvider.Issuer,
					strings.Join(provider.Spec.AllowedDomains, ", "),
				})
			}
			table.Render()
			return nil
		},
	}
}

func newIdentityProvidersGetCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "get <name>",
		Short: "Get a specific identity provider",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			data, err := c.Get(fmt.Sprintf("/api/identity-providers/%s", args[0]))
			if err != nil {
				return err
			}
			if isJSONOutput() {
				fmt.Println(string(data))
				return nil
			}

			var provider cliIdentityProviderResponse
			if err := json.Unmarshal(data, &provider); err != nil {
				return fmt.Errorf("failed to parse response: %w", err)
			}
			printIdentityProvider(provider)
			return nil
		},
	}
}

func newIdentityProvidersApplyCmd() *cobra.Command {
	var (
		filePath string
		name     string
	)
	cmd := &cobra.Command{
		Use:   "apply -f <file>",
		Short: "Create or update an identity provider from YAML or JSON",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if strings.TrimSpace(filePath) == "" {
				return fmt.Errorf("--file is required")
			}
			req, err := loadIdentityProviderApplyRequest(filePath, name)
			if err != nil {
				return err
			}
			c, err := newAPIClient()
			if err != nil {
				return err
			}

			action := "created"
			if _, err := c.Get(fmt.Sprintf("/api/identity-providers/%s", req.Name)); err == nil {
				action = "updated"
			} else if extractHTTPStatus(err) != httpStatusNotFound {
				return err
			}

			data, err := c.Post("/api/identity-providers", req)
			if err != nil {
				return err
			}
			return printAppliedIdentityProvider(req.Name, action, data)
		},
	}
	cmd.Flags().StringVarP(&filePath, "file", "f", "", "Identity provider YAML or JSON file")
	cmd.Flags().StringVar(&name, "name", "", "Override the identity provider name (required when the file contains only a raw spec)")
	return cmd
}

func newIdentityProvidersDeleteCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "delete <name>",
		Short: "Delete an identity provider",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			c, err := newAPIClient()
			if err != nil {
				return err
			}
			if err := c.Delete(fmt.Sprintf("/api/identity-providers/%s", args[0])); err != nil {
				return err
			}
			fmt.Printf("Identity provider %q deleted.\n", args[0])
			return nil
		},
	}
}

func loadIdentityProviderApplyRequest(path, nameOverride string) (cliIdentityProviderApplyRequest, error) {
	var req cliIdentityProviderApplyRequest
	if err := decodeStructuredFile(path, &req); err != nil {
		return cliIdentityProviderApplyRequest{}, err
	}

	if identityProviderSpecIsZero(req.Spec) {
		var spec cliIdentityProviderSpec
		if err := decodeStructuredFile(path, &spec); err != nil {
			return cliIdentityProviderApplyRequest{}, err
		}
		req.Spec = spec
	}
	if strings.TrimSpace(nameOverride) != "" {
		req.Name = strings.TrimSpace(nameOverride)
	}
	req.Name = strings.TrimSpace(req.Name)
	req.Namespace = strings.TrimSpace(req.Namespace)
	req.Spec.Host = strings.TrimSpace(req.Spec.Host)
	req.Spec.UserIDClaim = strings.TrimSpace(req.Spec.UserIDClaim)
	req.Spec.IdentityProvider.Issuer = strings.TrimSpace(req.Spec.IdentityProvider.Issuer)
	req.Spec.IdentityProvider.JWKSURI = strings.TrimSpace(req.Spec.IdentityProvider.JWKSURI)

	if req.Name == "" {
		return cliIdentityProviderApplyRequest{}, fmt.Errorf("identity provider name is required; provide it in the file or via --name")
	}
	if req.Spec.Host == "" {
		return cliIdentityProviderApplyRequest{}, fmt.Errorf("identity provider spec.host is required")
	}
	if req.Spec.IdentityProvider.Issuer == "" {
		return cliIdentityProviderApplyRequest{}, fmt.Errorf("identity provider spec.identityProvider.issuer is required")
	}
	if req.Spec.IdentityProvider.JWKSURI == "" {
		return cliIdentityProviderApplyRequest{}, fmt.Errorf("identity provider spec.identityProvider.jwksUri is required")
	}
	if req.Spec.UserIDClaim == "" {
		return cliIdentityProviderApplyRequest{}, fmt.Errorf("identity provider spec.userIDClaim is required")
	}

	return req, nil
}

func identityProviderSpecIsZero(spec cliIdentityProviderSpec) bool {
	return strings.TrimSpace(spec.Host) == "" &&
		strings.TrimSpace(spec.UserIDClaim) == "" &&
		strings.TrimSpace(spec.IdentityProvider.Issuer) == "" &&
		strings.TrimSpace(spec.IdentityProvider.JWKSURI) == "" &&
		len(spec.IdentityProvider.Audiences) == 0 &&
		len(spec.AllowedDomains) == 0
}

func printIdentityProvider(provider cliIdentityProviderResponse) {
	fmt.Printf("Name:         %s\n", provider.Name)
	fmt.Printf("Namespace:    %s\n", provider.Namespace)
	fmt.Printf("Host:         %s\n", provider.Spec.Host)
	fmt.Printf("User Claim:   %s\n", provider.Spec.UserIDClaim)
	fmt.Printf("Issuer:       %s\n", provider.Spec.IdentityProvider.Issuer)
	fmt.Printf("JWKS URI:     %s\n", provider.Spec.IdentityProvider.JWKSURI)
	if len(provider.Spec.IdentityProvider.Audiences) > 0 {
		fmt.Printf("Audiences:    %s\n", strings.Join(provider.Spec.IdentityProvider.Audiences, ", "))
	}
	if len(provider.Spec.AllowedDomains) > 0 {
		fmt.Printf("Domains:      %s\n", strings.Join(provider.Spec.AllowedDomains, ", "))
	}
}

func printAppliedIdentityProvider(name, action string, data []byte) error {
	if isJSONOutput() {
		fmt.Println(string(data))
		return nil
	}
	var provider cliIdentityProviderResponse
	if err := json.Unmarshal(data, &provider); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}
	fmt.Printf("Identity provider %q %s.\n", firstNonEmptyRunValue(provider.Name, name), action)
	fmt.Printf("Host: %s, user claim: %s\n", provider.Spec.Host, provider.Spec.UserIDClaim)
	return nil
}
