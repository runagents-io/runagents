# Identity Providers API

Configure identity providers to authenticate end users calling your agents. When a user makes a request to an agent, RunAgents validates their JWT token against the configured identity provider and propagates the user identity through to downstream tools via the `X-End-User-ID` header.

---

## List Identity Providers

<span class="method-get">GET</span> <span class="endpoint">/api/identity-providers</span>

Returns all registered identity providers.

=== "curl"

    ```bash
    curl https://api.runagents.io/api/identity-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
[
  {
    "name": "google-oidc",
    "namespace": "default",
    "spec": {
      "host": "portal.agents.example.com",
      "identityProvider": {
        "issuer": "https://accounts.google.com",
        "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
        "audiences": ["my-app.example.com"]
      },
      "userIDClaim": "email",
      "allowedDomains": ["example.com"]
    }
  }
]
```

---

## Create an Identity Provider

<span class="method-post">POST</span> <span class="endpoint">/api/identity-providers</span>

Register a new identity provider. Idempotent -- creating with an existing name updates it.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identity provider name |
| `namespace` | string | No | Namespace (defaults to `default`) |
| `spec` | object | Yes | Identity provider specification |

### Example: Google OIDC

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/identity-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "google-oidc",
        "spec": {
          "host": "portal.agents.example.com",
          "identityProvider": {
            "issuer": "https://accounts.google.com",
            "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
            "audiences": ["my-app.example.com"]
          },
          "userIDClaim": "email",
          "allowedDomains": ["example.com"]
        }
      }'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/api/identity-providers",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "name": "google-oidc",
            "spec": {
                "host": "portal.agents.example.com",
                "identityProvider": {
                    "issuer": "https://accounts.google.com",
                    "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
                    "audiences": ["my-app.example.com"],
                },
                "userIDClaim": "email",
                "allowedDomains": ["example.com"],
            },
        },
    )
    print(resp.json())
    ```

### Response (201 Created)

```json
{
  "name": "google-oidc",
  "namespace": "default",
  "spec": {
    "host": "portal.agents.example.com",
    "identityProvider": {
      "issuer": "https://accounts.google.com",
      "jwksUri": "https://www.googleapis.com/oauth2/v3/certs",
      "audiences": ["my-app.example.com"]
    },
    "userIDClaim": "email",
    "allowedDomains": ["example.com"]
  }
}
```

### Example: Auth0

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/identity-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "auth0-prod",
        "spec": {
          "host": "app.example.com",
          "identityProvider": {
            "issuer": "https://example.us.auth0.com/",
            "jwksUri": "https://example.us.auth0.com/.well-known/jwks.json",
            "audiences": ["https://api.example.com"]
          },
          "userIDClaim": "sub",
          "allowedDomains": ["example.com"]
        }
      }'
    ```

### Example: Okta

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/identity-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "okta-corp",
        "spec": {
          "host": "internal.example.com",
          "identityProvider": {
            "issuer": "https://example.okta.com/oauth2/default",
            "jwksUri": "https://example.okta.com/oauth2/default/v1/keys",
            "audiences": ["api://default"]
          },
          "userIDClaim": "email"
        }
      }'
    ```

---

## Get Identity Provider Details

<span class="method-get">GET</span> <span class="endpoint">/api/identity-providers/:name</span>

Retrieve details for a specific identity provider.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Identity provider name |

=== "curl"

    ```bash
    curl https://api.runagents.io/api/identity-providers/google-oidc \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

Returns the full identity provider object.

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `identity provider "google-oidc" not found` | Provider does not exist |

---

## Delete an Identity Provider

<span class="method-delete">DELETE</span> <span class="endpoint">/api/identity-providers/:name</span>

Delete an identity provider.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Identity provider name |

=== "curl"

    ```bash
    curl -X DELETE https://api.runagents.io/api/identity-providers/google-oidc \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
{
  "status": "deleted"
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `identity provider "google-oidc" not found` | Provider does not exist |

---

## Identity Provider Object Reference

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `host` | string | Yes | Public hostname for client apps (e.g., `portal.agents.example.com`) |
| `identityProvider` | object | Yes | OIDC/JWT provider configuration |
| `userIDClaim` | string | Yes | JWT claim to extract as the user identity (e.g., `email`, `sub`) |
| `allowedDomains` | string[] | No | Restrict access to specific email domains |

### Identity Provider Config

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issuer` | string | Yes | OIDC issuer URL (used to validate JWT `iss` claim) |
| `jwksUri` | string | Yes | JSON Web Key Set endpoint for token signature verification |
| `audiences` | string[] | No | Accepted JWT audiences (validates `aud` claim) |

### How Identity Propagation Works

1. End user authenticates with your app and obtains a JWT from the identity provider
2. Client app sends the JWT in the `Authorization: Bearer <token>` header when calling an agent
3. RunAgents validates the JWT signature using the JWKS endpoint
4. The `userIDClaim` (e.g., `email`) is extracted and injected as the `X-End-User-ID` header
5. This identity flows through to every tool call the agent makes
6. Tools receive the original user identity, enabling per-user authorization and audit trails

!!! tip "Choosing a user ID claim"
    Use `email` for human-readable identity propagation. Use `sub` if you need a stable, opaque identifier that does not change when users update their email.
