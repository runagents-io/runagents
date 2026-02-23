---
title: OAuth & Consent
description: How RunAgents handles OAuth2 three-legged authorization for tools that require end-user consent, including token management and automatic refresh.
---

# OAuth & Consent

Some tools require the end user to explicitly authorize access -- not just the platform. Google Drive, Slack, GitHub, and many other services use OAuth2 to ensure users consent to actions performed on their behalf. RunAgents handles this entire flow transparently.

---

## The Problem

Consider an agent that reads a user's Google Drive files. The agent needs to act *as that specific user*, not as a generic service account. Google requires the user to see a consent screen, approve the requested scopes, and grant a token. This is called **three-legged OAuth (3LO)**.

Without RunAgents, your agent code would need to:

- Detect when consent is needed
- Generate an authorization URL with the right scopes
- Handle the OAuth callback
- Store and refresh tokens per user
- Inject the token on every request

RunAgents handles all of this automatically.

---

## How It Works

### The Flow

```
Agent calls Google Drive tool
         |
         v
RunAgents checks for existing token
         |
    ┌────┴─────────────────────────┐
    |                              |
    v                              v
Token found                   No token
    |                              |
    v                              v
Inject token,              Return CONSENT_REQUIRED
forward request            with authorization_url
                                   |
                                   v
                           Client redirects user
                           to consent screen
                                   |
                                   v
                           User approves
                                   |
                                   v
                           OAuth callback receives code
                                   |
                                   v
                           RunAgents exchanges code for tokens
                           and stores per-user refresh token
                                   |
                                   v
                           Subsequent calls use
                           stored token automatically
```

### Step-by-Step

**1. Agent calls a tool configured with OAuth2**

Your agent makes a normal HTTP call to the tool URL. No OAuth logic in your code.

**2. RunAgents checks for a token**

The platform looks up tokens for this user + tool combination, following a priority order:

| Priority | Token Source | Description |
|---|---|---|
| 1st | Per-user refresh token | From a previous consent by this specific user |
| 2nd | Shared refresh token | A platform-wide token (e.g., for service-level access) |
| 3rd | None available | Consent is required |
| 4th | Client credentials | Falls back to client credentials grant if configured |

**3. If no token exists: CONSENT_REQUIRED**

The platform returns a `403` response to the agent with:

```json
{
  "error": "CONSENT_REQUIRED",
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&scope=...&state=..."
}
```

**4. Client app redirects the user**

Your client application receives the `CONSENT_REQUIRED` response (propagated from the agent) and redirects the user to the `authorization_url`. The user sees the OAuth provider's consent screen (e.g., "Allow RunAgents to access your Google Drive?").

**5. User approves**

The user clicks "Allow" on the consent screen. The OAuth provider redirects back to RunAgents' callback URL with an authorization code.

**6. RunAgents exchanges the code**

The platform exchanges the authorization code for an access token and refresh token, then stores the refresh token keyed to this specific user + tool combination.

**7. Subsequent calls work automatically**

The next time this user's agent calls the same tool, RunAgents finds the stored refresh token, obtains a fresh access token, and injects it. No further consent needed (until the user revokes access).

---

## Token Management

RunAgents manages the full token lifecycle:

| Action | Description |
|---|---|
| **Storage** | Refresh tokens are stored securely, keyed per user + tool |
| **Refresh** | Access tokens are refreshed automatically when they expire |
| **Isolation** | Each user's tokens are independent -- revoking one user's access does not affect others |
| **Injection** | The access token is injected as `Authorization: Bearer <token>` on the outbound request |

!!! info "Tokens never reach your agent code"

    Your agent code never sees OAuth tokens. The platform injects them at the egress layer, after policy evaluation. This prevents token leakage and simplifies your agent implementation.

---

## Security

### CSRF Protection

The OAuth state parameter is HMAC-signed by RunAgents. When the callback is received, the platform verifies the signature before exchanging the code. This prevents cross-site request forgery attacks.

### Per-User Consent

Each user's consent is independent. User A authorizing access to Google Drive does not grant access for User B. The platform maintains separate refresh tokens per user + tool combination.

### Automatic Token Refresh

Access tokens have short lifetimes (typically 1 hour). RunAgents automatically refreshes them using the stored refresh token, so users are not repeatedly asked for consent.

### Revocation

If a user revokes access at the OAuth provider (e.g., removes the app from their Google account), the stored refresh token becomes invalid. The next tool call returns `CONSENT_REQUIRED` again, prompting a new consent flow.

---

## Configuration

To enable OAuth2 on a tool, configure the following when registering the tool:

| Setting | Description | Example |
|---|---|---|
| **Auth Type** | Set to `OAuth2` | `OAuth2` |
| **Authorization URL** | The provider's authorization endpoint | `https://accounts.google.com/o/oauth2/auth` |
| **Token URL** | The provider's token exchange endpoint | `https://oauth2.googleapis.com/token` |
| **Scopes** | The OAuth scopes to request | `https://www.googleapis.com/auth/drive.readonly` |
| **Credentials** | A secret containing `client_id` and `client_secret` | Created via the console or API |

=== "Console"

    When registering a tool, select **OAuth2** as the authentication type and fill in the authorization URL, token URL, scopes, and credentials.

=== "API"

    ```bash
    curl -X POST https://your-platform/api/tools \
      -H "Content-Type: application/json" \
      -d '{
        "name": "google-drive",
        "baseUrl": "https://www.googleapis.com",
        "auth": {
          "type": "OAuth2",
          "authUrl": "https://accounts.google.com/o/oauth2/auth",
          "tokenUrl": "https://oauth2.googleapis.com/token",
          "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
          "credentialsSecret": "google-drive-oauth-creds"
        }
      }'
    ```

!!! warning "Callback URL configuration"

    You must add RunAgents' OAuth callback URL to the OAuth provider's allowed redirect URIs. The callback URL is provided in your platform settings. Without this, the OAuth provider will reject the callback.

---

## Handling CONSENT_REQUIRED in Your Client App

When your client application receives a `CONSENT_REQUIRED` response, it should:

1. Parse the `authorization_url` from the response body
2. Redirect the user to that URL (or open it in a popup/new tab)
3. After the user completes consent, retry the original request

```javascript
// Example client-side handling
const response = await fetch('/agent/invoke', { method: 'POST', body: payload });

if (response.status === 403) {
  const data = await response.json();
  if (data.error === 'CONSENT_REQUIRED') {
    // Redirect user to OAuth consent screen
    window.location.href = data.authorization_url;
  }
}
```

After consent, the user is redirected back to your application. Retrying the original request will succeed because RunAgents now has a valid token for that user.

---

## Next Steps

- [Identity Propagation](identity-propagation.md) -- How user identity enables per-user token lookup
- [Policy Model](policy-model.md) -- Policy evaluation happens before token injection
- [Troubleshooting](../operations/troubleshooting.md) -- Common OAuth issues and how to resolve them
