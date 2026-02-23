# Model Providers API

Configure LLM model providers that your agents use for inference. RunAgents acts as a unified gateway -- agents call a single endpoint and the platform handles credential injection, format translation, and provider routing.

---

## List Model Providers

<span class="method-get">GET</span> <span class="endpoint">/api/model-providers</span>

Returns all registered model providers.

=== "curl"

    ```bash
    curl https://api.runagents.io/api/model-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

```json
[
  {
    "name": "openai-prod",
    "namespace": "agent-system",
    "spec": {
      "provider": "openai",
      "endpoint": "https://api.openai.com",
      "models": ["gpt-4o", "gpt-4o-mini", "text-embedding-3-small"],
      "auth": {
        "type": "APIKey",
        "apiKeyConfig": {
          "in": "Header",
          "name": "Authorization",
          "valuePrefix": "Bearer ",
          "secretRef": {"name": "openai-api-key"}
        }
      },
      "rateLimit": {
        "requestsPerMinute": 500
      }
    },
    "status": {
      "phase": "Available",
      "message": ""
    }
  }
]
```

---

## Create a Model Provider

<span class="method-post">POST</span> <span class="endpoint">/api/model-providers</span>

Register a new model provider. Idempotent -- creating with an existing name updates it.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique provider name |
| `spec` | object | Yes | Provider specification (see [Model Provider Object Reference](#model-provider-object-reference)) |

### Example: OpenAI provider

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/model-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "openai-prod",
        "spec": {
          "provider": "openai",
          "endpoint": "https://api.openai.com",
          "models": ["gpt-4o", "gpt-4o-mini"],
          "auth": {
            "type": "APIKey",
            "apiKeyConfig": {
              "in": "Header",
              "name": "Authorization",
              "valuePrefix": "Bearer ",
              "secretRef": {"name": "openai-api-key"}
            }
          },
          "rateLimit": {
            "requestsPerMinute": 500
          }
        }
      }'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/api/model-providers",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "name": "openai-prod",
            "spec": {
                "provider": "openai",
                "endpoint": "https://api.openai.com",
                "models": ["gpt-4o", "gpt-4o-mini"],
                "auth": {
                    "type": "APIKey",
                    "apiKeyConfig": {
                        "in": "Header",
                        "name": "Authorization",
                        "valuePrefix": "Bearer ",
                        "secretRef": {"name": "openai-api-key"},
                    },
                },
                "rateLimit": {"requestsPerMinute": 500},
            },
        },
    )
    print(resp.json())
    ```

### Response (201 Created)

```json
{
  "name": "openai-prod",
  "namespace": "agent-system",
  "spec": {
    "provider": "openai",
    "endpoint": "https://api.openai.com",
    "models": ["gpt-4o", "gpt-4o-mini"],
    "auth": {
      "type": "APIKey",
      "apiKeyConfig": {
        "in": "Header",
        "name": "Authorization",
        "valuePrefix": "Bearer ",
        "secretRef": {"name": "openai-api-key"}
      }
    },
    "rateLimit": {
      "requestsPerMinute": 500
    }
  },
  "status": {
    "phase": "Pending",
    "message": ""
  }
}
```

### Example: AWS Bedrock provider

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/model-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "bedrock-us-east",
        "spec": {
          "provider": "bedrock",
          "endpoint": "https://bedrock-runtime.us-east-1.amazonaws.com",
          "models": [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-haiku-20240307-v1:0"
          ],
          "auth": {
            "type": "AWSSignature",
            "awsConfig": {
              "region": "us-east-1",
              "credentialsSecretRef": {
                "name": "bedrock-aws-credentials"
              }
            }
          }
        }
      }'
    ```

### Example: Anthropic provider

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/model-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "anthropic-prod",
        "spec": {
          "provider": "anthropic",
          "endpoint": "https://api.anthropic.com",
          "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
          "auth": {
            "type": "APIKey",
            "apiKeyConfig": {
              "in": "Header",
              "name": "x-api-key",
              "secretRef": {"name": "anthropic-api-key"}
            }
          }
        }
      }'
    ```

### Example: Ollama (local inference)

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/model-providers \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "ollama-local",
        "spec": {
          "provider": "ollama",
          "endpoint": "http://ollama.internal:11434",
          "models": ["llama3.1", "mistral"],
          "auth": {
            "type": "None"
          }
        }
      }'
    ```

---

## Get Model Provider Details

<span class="method-get">GET</span> <span class="endpoint">/api/model-providers/:name</span>

Retrieve details for a specific model provider.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Model provider name |

=== "curl"

    ```bash
    curl https://api.runagents.io/api/model-providers/openai-prod \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

Returns the full model provider object.

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `model provider "openai-prod" not found` | Provider does not exist |

---

## Delete a Model Provider

<span class="method-delete">DELETE</span> <span class="endpoint">/api/model-providers/:name</span>

Delete a model provider.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Model provider name |

=== "curl"

    ```bash
    curl -X DELETE https://api.runagents.io/api/model-providers/openai-prod \
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
| `404` | `model provider "openai-prod" not found` | Provider does not exist |

---

## Model Provider Object Reference

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Backend type: `openai`, `anthropic`, `bedrock`, `ollama` |
| `endpoint` | string | Yes | Provider API endpoint URL |
| `models` | string[] | Yes | List of supported model IDs |
| `auth` | object | Yes | Authentication configuration |
| `rateLimit` | object | No | Rate limiting configuration |

### Authentication Types

| Type | Description | Required Config |
|------|-------------|-----------------|
| `APIKey` | API key injected as header or query parameter | `apiKeyConfig` |
| `AWSSignature` | AWS SigV4 request signing for Bedrock | `awsConfig` |
| `OAuth2` | OAuth2 token-based authentication | `oauth2Config` |
| `None` | No authentication (e.g., local Ollama) | -- |

### AWS Config

| Field | Type | Description |
|-------|------|-------------|
| `region` | string | AWS region (e.g., `us-east-1`) |
| `credentialsSecretRef` | object | Reference to stored AWS credentials (`aws_access_key_id`, `aws_secret_access_key`) |

### Rate Limit

| Field | Type | Description |
|-------|------|-------------|
| `requestsPerMinute` | integer | Maximum requests per minute |

### Status Phases

| Phase | Description |
|-------|-------------|
| `Pending` | Provider is being configured |
| `Available` | Provider is healthy and ready to serve requests |
| `Unavailable` | Provider endpoint is unreachable |
| `Failed` | Provider configuration error |

### Supported Providers

| Provider | Format Translation | Auth Method | Notes |
|----------|-------------------|-------------|-------|
| `openai` | Passthrough | APIKey | Standard OpenAI API |
| `anthropic` | OpenAI to Messages API | APIKey | Automatic format translation |
| `bedrock` | OpenAI to Bedrock | AWSSignature (SigV4) | AWS-native inference |
| `ollama` | OpenAI to Ollama | None | Local/self-hosted inference |

---

## Calling Models — LLM Gateway

Once a model provider is registered, your agents call it through the **RunAgents LLM Gateway** — a single OpenAI-compatible endpoint. The gateway handles credential injection, format translation, and provider routing automatically.

<span class="method-post">POST</span> <span class="endpoint">/v1/chat/completions</span>


The LLM Gateway provides an **OpenAI-compatible** endpoint for all configured model providers. Agents call a single endpoint and the gateway handles credential injection, format translation, and provider routing. Your agent code never touches API keys.

---

## Chat Completions

<span class="method-post">POST</span> <span class="endpoint">/v1/chat/completions</span>

Send a chat completion request using the standard OpenAI format. The gateway matches the requested model against registered model providers and routes the request accordingly.

### Request Body

The request body follows the [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat) format:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model identifier (must match a model in a registered provider) |
| `messages` | object[] | Yes | Array of message objects with `role` and `content` |
| `temperature` | number | No | Sampling temperature (0-2). Defaults to 1 |
| `max_tokens` | integer | No | Maximum tokens to generate |
| `stream` | boolean | No | Enable streaming responses |
| `top_p` | number | No | Nucleus sampling parameter |
| `frequency_penalty` | number | No | Frequency penalty (-2 to 2) |
| `presence_penalty` | number | No | Presence penalty (-2 to 2) |
| `stop` | string or string[] | No | Stop sequences |

### Example: Standard request

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/v1/chat/completions \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "gpt-4o-mini",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "What is the capital of France?"}
        ],
        "temperature": 0.7
      }'
    ```

=== "Python"

    ```python
    import requests

    resp = requests.post(
        "https://api.runagents.io/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"},
            ],
            "temperature": 0.7,
        },
    )
    print(resp.json()["choices"][0]["message"]["content"])
    ```

=== "Python (OpenAI SDK)"

    ```python
    from openai import OpenAI

    # Point the OpenAI SDK at the RunAgents gateway
    client = OpenAI(
        base_url="https://api.runagents.io/v1",
        api_key="your-runagents-api-key",
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"},
        ],
        temperature=0.7,
    )
    print(response.choices[0].message.content)
    ```

### Response (200 OK)

The response follows the OpenAI format regardless of the backend provider:

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1709123456,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 8,
    "total_tokens": 33
  }
}
```

### Example: Using an Anthropic model through the gateway

The gateway automatically translates between OpenAI and Anthropic formats:

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/v1/chat/completions \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
          {"role": "user", "content": "Explain quantum computing in one paragraph."}
        ],
        "max_tokens": 200
      }'
    ```

The response is returned in OpenAI format even though the backend is Anthropic.

### Example: Using a Bedrock model

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/v1/chat/completions \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "messages": [
          {"role": "user", "content": "Summarize this document."}
        ]
      }'
    ```

The gateway signs the request with AWS SigV4 credentials automatically.

---

## How the Gateway Works

```
Agent                    LLM Gateway                   Provider
  |                          |                            |
  |  POST /v1/chat/completions                            |
  |  model: "gpt-4o-mini"   |                            |
  |------------------------->|                            |
  |                          |  1. Match model to         |
  |                          |     ModelProvider           |
  |                          |  2. Read credentials        |
  |                          |  3. Translate format        |
  |                          |     (if needed)             |
  |                          |                            |
  |                          |  POST (provider-specific)   |
  |                          |  + Authorization header     |
  |                          |--------------------------->|
  |                          |                            |
  |                          |  Provider response          |
  |                          |<---------------------------|
  |                          |                            |
  |                          |  4. Translate to OpenAI     |
  |                          |     format (if needed)      |
  |                          |                            |
  |  OpenAI-format response  |                            |
  |<-------------------------|                            |
```

### Step-by-step:

1. **Model matching** -- The gateway looks up which registered `ModelProvider` supports the requested model name
2. **Credential injection** -- Reads the provider's credentials (API key, AWS credentials, etc.) and adds them to the request
3. **Format translation** -- Converts the OpenAI-format request to the provider's native format if needed:
    - **OpenAI**: Passthrough (no translation)
    - **Anthropic**: Translates to the Anthropic Messages API format
    - **Bedrock**: Translates to Bedrock's invoke format with SigV4 signing
    - **Ollama**: Translates to Ollama's chat API format
4. **Response normalization** -- Converts the provider's response back to OpenAI format

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `400` | `model is required` | Missing model field in request |
| `404` | `no provider found for model "..."` | No registered ModelProvider supports this model |
| `502` | `provider request failed` | Backend provider returned an error |

---

## Supported Providers

| Provider | Models (examples) | Authentication | Format |
|----------|-------------------|----------------|--------|
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `text-embedding-3-small` | API Key | Native (passthrough) |
| **Anthropic** | `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307` | API Key | Auto-translated from OpenAI format |
| **AWS Bedrock** | `anthropic.claude-3-5-sonnet-*`, `amazon.titan-*` | AWS SigV4 | Auto-translated with SigV4 signing |
| **Ollama** | `llama3.1`, `mistral`, `codellama` | None | Auto-translated to Ollama format |

!!! tip "Using the OpenAI SDK"
    Since the gateway is OpenAI-compatible, you can use the official OpenAI Python or Node.js SDK by pointing `base_url` at your RunAgents gateway URL. This means existing code that uses the OpenAI SDK works with any backend provider without changes.

!!! note "Credentials stay on the platform"
    API keys and AWS credentials are stored securely in the platform and injected at the gateway layer. Agent code never has access to provider credentials.
