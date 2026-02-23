# Model Providers

Model providers connect your agents to large language models (LLMs). RunAgents supports OpenAI, Anthropic, AWS Bedrock, and self-hosted Ollama out of the box. Register a provider once, and any agent on the platform can use it through a single, unified API.

Navigate to **Models** in the sidebar, then click **+ New Model Provider**.

---

## Model Provider Configuration

| Field | Description | Required |
|-------|-------------|----------|
| **Provider type** | The LLM backend: `OpenAI`, `Anthropic`, `Bedrock`, or `Ollama` | Yes |
| **Endpoint** | The provider's API URL (e.g., `https://api.openai.com`) | Yes |
| **Models** | List of model IDs this provider supports (e.g., `gpt-4o`, `gpt-4o-mini`, `claude-sonnet-4-20250514`) | Yes |

---

## Authentication

Choose the authentication method for the provider.

### API Key

For **OpenAI** and **Anthropic** providers. Provide the API key secret; the platform injects it into every request.

| Field | Description |
|-------|-------------|
| **Header name** | Where to inject the key (e.g., `Authorization`) |
| **Value prefix** | Text prepended to the key (e.g., `Bearer `) |
| **Secret** | The stored secret containing the API key |

### AWS Signature

For **AWS Bedrock** providers. The platform signs requests with SigV4 automatically.

| Field | Description |
|-------|-------------|
| **Region** | AWS region (e.g., `us-east-1`) |
| **Credentials** | Secret containing `aws_access_key_id` and `aws_secret_access_key` |

### OAuth2

For custom providers that require OAuth2 authentication. Configure authorization URL, token URL, scopes, and client credentials.

### None

For **Ollama** and other self-hosted models that run without authentication.

---

## How the LLM Gateway Works

From your agent's perspective, using language models is simple:

1. **Single endpoint** -- Your agent calls `/v1/chat/completions` (an OpenAI-compatible API). This is the only URL your agent needs.

2. **Model-based routing** -- Include the model name in your request (e.g., `gpt-4o`, `claude-sonnet-4-20250514`, `us.anthropic.claude-opus-4-6-v1`). The gateway looks up which registered model provider supports that model and routes the request there.

3. **Automatic format translation** -- If the upstream provider uses a different API format (e.g., Anthropic's Messages API or AWS Bedrock's InvokeModel), the gateway translates the request and response transparently. Your code always uses the OpenAI chat completions format.

4. **Credentials managed by the platform** -- API keys, AWS credentials, and OAuth tokens are injected by the gateway. Your agent code never handles or stores provider credentials.

```python
# Your agent code -- same format regardless of provider
import urllib.request, json

body = {
    "model": "gpt-4o-mini",  # or "claude-sonnet-4-20250514", "us.anthropic.claude-opus-4-6-v1", etc.
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is RunAgents?"},
    ],
}

req = urllib.request.Request(
    f"{LLM_GATEWAY_URL}/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    print(result["choices"][0]["message"]["content"])
```

!!! info "Multi-model agents"
    Agents can use multiple models with different roles. For example, use a fast model for chat and a larger model for complex reasoning. During the Wire step of deployment, you map each detected model usage to a registered provider and select the specific model.

---

## Supported Providers

| Provider | Endpoint | Auth Type | Format |
|----------|----------|-----------|--------|
| **OpenAI** | `https://api.openai.com` | API Key | Native (passthrough) |
| **Anthropic** | `https://api.anthropic.com` | API Key | Translated to/from Messages API |
| **AWS Bedrock** | `https://bedrock-runtime.{region}.amazonaws.com` | AWS Signature (SigV4) | Translated to/from InvokeModel |
| **Ollama** | `http://localhost:11434` (or your host) | None | Translated to/from Ollama format |

---

## Rate Limiting

You can optionally configure a **requests-per-minute** cap on a model provider to prevent runaway costs or quota exhaustion.

| Field | Description |
|-------|-------------|
| **Requests per minute** | Maximum number of requests allowed per minute |

!!! warning "Rate limiting is not yet enforced"
    The rate limit field is available for configuration, but enforcement is not yet active in the current release. This will be enabled in a future update.

---

## Model Provider Status

| Status | Meaning |
|--------|---------|
| **Available** | Provider is reachable and credentials are valid |
| **Unavailable** | Provider endpoint is unreachable or credentials are invalid |
| **Failed** | Configuration error; check the status message for details |

---

## Built-in Playground LLM

The **playground-llm** is a built-in model provider included in the RunAgents starter kit. It is created when you click **Deploy Hello World Agent** on the Dashboard or **Add starter Playground LLM** on the Models page.

- **Provider**: OpenAI
- **Models**: `gpt-4o-mini`
- **Authentication**: API Key (uses the platform's configured key)

The playground LLM allows you to test the full deploy and wiring flow without configuring your own provider credentials.

---

## What's Next

| Goal | Where to go |
|------|------------|
| Deploy an agent with this model | [Deploying Agents](deploying-agents.md) |
| Register tools for your agent | [Registering Tools](registering-tools.md) |
| Set up user authentication | [Identity Providers](identity-providers.md) |
