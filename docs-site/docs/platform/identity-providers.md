# Identity Providers

Identity providers connect RunAgents to your authentication system. When configured, RunAgents validates JWTs from client applications at the ingress, extracts the user identity, and propagates it through the entire request chain -- from client to agent to tool. This enables per-user access control, audit logging, and OAuth consent flows.

Navigate to **Identity** in the sidebar, then click **+ New Identity Provider**.

---

## Identity Provider Configuration

| Field | Description | Required |
|-------|-------------|----------|
| **Host** | The public hostname for client applications that will call your agents (e.g., `portal.myapp.com`) | Yes |
| **Issuer** | The OIDC issuer URL that signs JWTs (e.g., `https://accounts.google.com`, `https://login.microsoftonline.com/{tenant}/v2.0`) | Yes |
| **Public Keys URL (JWKS)** | The endpoint serving the JSON Web Key Set for JWT signature verification (e.g., `https://accounts.google.com/.well-known/jwks.json`) | Yes |
| **Audiences** | Accepted JWT audience values; tokens with other audiences are rejected | No |
| **User ID Claim** | The JWT claim that maps to the end-user identity (e.g., `email`, `sub`, `preferred_username`) | Yes |
| **Allowed Domains** | Restrict access by email domain -- only users with matching domains can authenticate (e.g., `company.com`) | No |

---

## How Identity Propagation Works

Once an identity provider is configured, here is what happens when a client application sends a request to an agent:

```
Client App            RunAgents Ingress        Agent           Tool (e.g., Stripe)
    |                       |                    |                    |
    |-- JWT in Auth header ->|                    |                    |
    |                       |-- Validate JWT      |                    |
    |                       |-- Extract user ID   |                    |
    |                       |-- X-End-User-ID --->|                    |
    |                       |                    |-- Call tool ------->|
    |                       |                    |  (X-End-User-ID    |
    |                       |                    |   header included) |
```

1. **Client authenticates**: The client application includes a JWT in the `Authorization` header.
2. **JWT validation**: RunAgents validates the JWT signature using the JWKS endpoint, checks the issuer and audience, and verifies the token has not expired.
3. **User identity extraction**: The configured `userIDClaim` (e.g., `email`) is extracted from the JWT.
4. **Identity propagation**: The extracted identity is set as the `X-End-User-ID` header and flows through the entire chain -- from the ingress to the agent to every tool the agent calls.

---

## What Identity Providers Enable

### Per-User Access Control

Tools and policies can reference user identities. For example, you can create a policy that allows only users from the `engineering` group to access the GitHub API, or restrict a specific user to read-only operations on a financial tool.

### Per-User OAuth Consent

When an agent calls a tool with OAuth2 authentication, the consent flow is per-user. Each user grants their own authorization to the tool (e.g., granting access to their Google Drive). The platform stores per-user refresh tokens and uses them automatically on subsequent requests.

### Audit Trail

Every tool call includes the authenticated user identity. This means audit logs can answer not just "which agent called Stripe?" but "which user's request caused that agent to call Stripe?"

### Domain-Based Access Control

The **Allowed Domains** field lets you restrict which users can access your agents. For example, setting `company.com` ensures only `@company.com` email addresses are accepted, even if the JWT issuer serves tokens for other domains.

---

## Common Identity Provider Configurations

### Google Workspace

| Field | Value |
|-------|-------|
| Issuer | `https://accounts.google.com` |
| Public Keys URL | `https://www.googleapis.com/oauth2/v3/certs` |
| User ID Claim | `email` |
| Allowed Domains | `yourcompany.com` |

### Microsoft Entra ID (Azure AD)

| Field | Value |
|-------|-------|
| Issuer | `https://login.microsoftonline.com/{tenant-id}/v2.0` |
| Public Keys URL | `https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys` |
| User ID Claim | `preferred_username` or `email` |

### Auth0

| Field | Value |
|-------|-------|
| Issuer | `https://{your-domain}.auth0.com/` |
| Public Keys URL | `https://{your-domain}.auth0.com/.well-known/jwks.json` |
| User ID Claim | `email` or `sub` |

### Okta

| Field | Value |
|-------|-------|
| Issuer | `https://{your-domain}.okta.com/oauth2/default` |
| Public Keys URL | `https://{your-domain}.okta.com/oauth2/default/v1/keys` |
| User ID Claim | `email` |

---

## Using Identity Providers During Agent Deployment

During the **Wire** step of the [deploy wizard](deploying-agents.md), you can choose an access mode for your agent:

- **Open** -- No authentication; any client can call the agent.
- **Authenticated** -- Requires a valid JWT from a registered identity provider. Select which provider to use.

When **Authenticated** is selected and only one identity provider is registered, it is auto-selected for convenience.

---

## What's Next

| Goal | Where to go |
|------|------------|
| Deploy an authenticated agent | [Deploying Agents](deploying-agents.md) |
| Register tools with per-user OAuth | [Registering Tools](registering-tools.md) |
| Understand the approval workflow | [Approvals](approvals.md) |
| Learn more about identity architecture | [Identity Propagation](../concepts/identity-propagation.md) |
