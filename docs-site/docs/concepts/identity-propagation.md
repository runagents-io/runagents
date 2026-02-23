---
title: Identity Propagation
description: How RunAgents propagates user identity end-to-end, from client application through agent to external tool, using cryptographically verified headers.
---

# Identity Propagation

RunAgents ensures that user identity flows from the client application, through the agent, to every external tool the agent calls. This happens automatically and transparently -- no code changes needed in your agent.

---

## The Five-Step Flow

### Step 1: Client Authenticates

The end user logs into your client application and receives a JWT (JSON Web Token) from your identity provider (e.g., Auth0, Okta, Firebase Auth, or any OIDC-compliant provider).

```
User ──login──> Your App ──JWT──> RunAgents
```

### Step 2: Ingress Validates

When a request carrying the JWT reaches RunAgents, the platform validates it:

- **Signature verification** -- The JWT signature is checked against your identity provider's JWKS (JSON Web Key Set) endpoint
- **Audience check** -- The `aud` claim must match the expected audience for your agent
- **Expiry check** -- Expired tokens are rejected

!!! warning "Invalid tokens are rejected at the edge"

    Requests with missing, malformed, or invalid JWTs never reach your agent. The platform returns a `401 Unauthorized` response before the request enters the agent runtime.

### Step 3: Identity Header Injected

After validation, the platform extracts the configured claim from the JWT payload and injects it as an HTTP header:

```
X-End-User-ID: user@example.com
```

The claim used is configurable per identity provider. Common choices:

| Claim | Example Value | Use Case |
|---|---|---|
| `email` | `user@example.com` | Human-readable, good for audit logs |
| `sub` | `auth0|abc123` | Stable unique identifier |
| `preferred_username` | `jdoe` | Display-friendly username |

### Step 4: Agent Receives Identity

Your agent receives every request with the `X-End-User-ID` header already set. The agent can read this header to personalize responses or pass it along, but it does not need to do anything special -- the platform handles forwarding automatically.

```python
# Your agent code -- identity is already in the header
def handle_request(request):
    user_id = request.headers.get("X-End-User-ID")
    # user_id = "user@example.com"
```

### Step 5: Tool Receives User Context

When the agent calls an external tool, the `X-End-User-ID` header is forwarded automatically. The external API receives:

- `X-End-User-ID: user@example.com` -- the verified end-user identity
- `Authorization: Bearer <token>` -- the tool's authentication credentials (injected by the platform)

The tool can use the user identity for per-user behavior: audit logging, data scoping, authorization decisions, or personalization.

---

## Two Layers of Identity

RunAgents maintains two distinct identities for every request:

| Identity | What It Represents | How It Is Established |
|---|---|---|
| **User identity** | The end user who triggered the agent | Extracted from JWT via configurable claim, forwarded as `X-End-User-ID` |
| **Agent identity** | The specific agent making the outbound call | Assigned by the platform via SPIFFE (a cryptographic workload identity standard) |

Both identities are available at the egress layer. This means the platform can answer two questions on every tool call:

1. **Which agent** is making this request?
2. **On behalf of which user?**

!!! info "Agent identity is used for policy evaluation"

    The platform uses the agent's identity (not the user's identity) to evaluate policies. This means you grant permissions to agents, not to users. The user's identity is forwarded for downstream context, not for access control within RunAgents.

---

## Security Properties

### Cryptographic Verification

User identity is not self-reported. The JWT is verified against the identity provider's public keys (JWKS). A forged or tampered token is rejected.

### Platform-Controlled Injection

The `X-End-User-ID` header is injected by the platform after token validation. Your agent code cannot forge or modify this header on outbound requests -- the egress layer controls what headers reach external tools.

### Per-User Isolation

Each user's identity is independent. When two users trigger the same agent, each request carries its own verified `X-End-User-ID`. Tools receive the correct user context for each call.

### No Token Leakage

Your agent code never sees the raw JWT or any authentication tokens for external tools. The platform strips the incoming JWT after extracting the identity claim and injects tool-specific credentials at the egress layer.

---

## Use Cases

**Per-user audit trails**
:   External tools log which user each action was performed for, enabling compliance and forensics.

**User-scoped data access**
:   A tool like Google Drive can return only the files belonging to the identified user.

**OAuth consent per user**
:   When a tool requires OAuth2 authorization, RunAgents manages per-user consent and tokens. See [OAuth & Consent](oauth-consent.md).

**Compliance logging**
:   Every request through the platform carries verified identity, providing a complete chain of custody for regulated environments.

**Multi-tenant agents**
:   A single agent deployment can serve multiple users, with each user's requests correctly attributed and isolated.

---

## Configuration

Identity propagation is configured when you register an identity provider:

| Setting | Description |
|---|---|
| **Issuer** | The JWT issuer URL (e.g., `https://your-domain.auth0.com/`) |
| **Audience** | Expected audience claim value |
| **JWKS URL** | Public key endpoint for signature verification (usually `{issuer}/.well-known/jwks.json`) |
| **User ID Claim** | Which JWT claim to extract as the user identity (default: `email`) |
| **Allowed Domains** | Which client domains can send requests to agents under this identity provider |

Set these up in the console under **Identity** or via the [API](../api/identity-providers.md).

---

## Next Steps

- [Policy Model](policy-model.md) -- How the platform uses agent identity (not user identity) for access control
- [OAuth & Consent](oauth-consent.md) -- How per-user OAuth consent works alongside identity propagation
- [Architecture](architecture.md) -- See how identity propagation fits into the three-stage request flow
