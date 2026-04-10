package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadIdentityProviderApplyRequestEnvelope(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "idp.yaml")
	if err := os.WriteFile(path, []byte(`
name: google-oidc
namespace: default
spec:
  host: portal.example.com
  identityProvider:
    issuer: https://accounts.google.com
    jwksUri: https://www.googleapis.com/oauth2/v3/certs
    audiences:
      - portal.example.com
  userIDClaim: email
  allowedDomains:
    - example.com
`), 0o600); err != nil {
		t.Fatalf("write idp file: %v", err)
	}

	req, err := loadIdentityProviderApplyRequest(path, "")
	if err != nil {
		t.Fatalf("loadIdentityProviderApplyRequest: %v", err)
	}
	if req.Name != "google-oidc" {
		t.Fatalf("expected name google-oidc, got %q", req.Name)
	}
	if req.Spec.Host != "portal.example.com" {
		t.Fatalf("expected host portal.example.com, got %q", req.Spec.Host)
	}
	if req.Spec.IdentityProvider.Issuer != "https://accounts.google.com" {
		t.Fatalf("unexpected issuer: %q", req.Spec.IdentityProvider.Issuer)
	}
}

func TestLoadIdentityProviderApplyRequestRawSpecWithOverride(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "idp.json")
	if err := os.WriteFile(path, []byte(`{
  "host": "portal.example.com",
  "identityProvider": {
    "issuer": "https://example.us.auth0.com/",
    "jwksUri": "https://example.us.auth0.com/.well-known/jwks.json",
    "audiences": ["https://api.example.com"]
  },
  "userIDClaim": "sub"
}`), 0o600); err != nil {
		t.Fatalf("write idp file: %v", err)
	}

	req, err := loadIdentityProviderApplyRequest(path, "auth0-prod")
	if err != nil {
		t.Fatalf("loadIdentityProviderApplyRequest: %v", err)
	}
	if req.Name != "auth0-prod" {
		t.Fatalf("expected override name auth0-prod, got %q", req.Name)
	}
	if req.Spec.UserIDClaim != "sub" {
		t.Fatalf("expected userIDClaim sub, got %q", req.Spec.UserIDClaim)
	}
}

func TestLoadIdentityProviderApplyRequestRequiresName(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "idp.yaml")
	if err := os.WriteFile(path, []byte(`
host: portal.example.com
identityProvider:
  issuer: https://accounts.google.com
  jwksUri: https://www.googleapis.com/oauth2/v3/certs
userIDClaim: email
`), 0o600); err != nil {
		t.Fatalf("write idp file: %v", err)
	}

	if _, err := loadIdentityProviderApplyRequest(path, ""); err == nil {
		t.Fatalf("expected missing name error")
	}
}

func TestLoadIdentityProviderApplyRequestRequiresOIDCFields(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "idp.yaml")
	if err := os.WriteFile(path, []byte(`
name: broken-idp
spec:
  host: portal.example.com
  identityProvider:
    issuer: https://accounts.google.com
  userIDClaim: email
`), 0o600); err != nil {
		t.Fatalf("write idp file: %v", err)
	}

	if _, err := loadIdentityProviderApplyRequest(path, ""); err == nil {
		t.Fatalf("expected missing jwksUri validation error")
	}
}
