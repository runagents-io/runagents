# Ingestion API

The Ingestion API analyzes agent source code to automatically detect tools, model providers, secrets, outbound destinations, and dependencies. This powers the deploy wizard's auto-wiring feature and can be used standalone for code analysis.

---

## Analyze Source Files

<span class="method-post">POST</span> <span class="endpoint">/analyze</span>

Analyze source files to detect tools, models, secrets, and dependencies. Results are cached for 1 hour.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | object | Yes | Map of filename to source code content |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/analyze \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "files": {
          "agent.py": "import openai\nimport requests\n\nclient = openai.OpenAI()\n\ndef run():\n    # Call Stripe API\n    resp = requests.get(\"https://api.stripe.com/v1/charges\",\n        headers={\"Authorization\": \"Bearer sk_live_abc123\"})\n    \n    # Get LLM response\n    completion = client.chat.completions.create(\n        model=\"gpt-4o\",\n        messages=[{\"role\": \"user\", \"content\": \"Summarize charges\"}]\n    )\n    return completion.choices[0].message.content\n"
        }
      }'
    ```

=== "Python"

    ```python
    import requests

    with open("agent.py") as f:
        code = f.read()

    resp = requests.post(
        "https://api.runagents.io/analyze",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"files": {"agent.py": code}},
    )
    analysis = resp.json()
    print(f"Detected tools: {[t['name'] for t in analysis['tools']]}")
    print(f"Detected models: {[m['model'] for m in analysis['model_providers']]}")
    print(f"Secrets found: {len(analysis['secrets'])}")
    ```

### Response (201 Created)

```json
{
  "id": "analysis-a1b2c3d4",
  "tools": [
    {
      "name": "stripe-api",
      "base_url": "https://api.stripe.com",
      "file": "agent.py",
      "line": 8
    }
  ],
  "model_providers": [
    {
      "provider": "openai",
      "model": "gpt-4o"
    }
  ],
  "model_usages": [
    {
      "role": "default",
      "variable_name": "client",
      "file": "agent.py",
      "line": 3
    }
  ],
  "secrets": [
    {
      "type": "api_key",
      "file": "agent.py",
      "line": 9,
      "severity": "high"
    }
  ],
  "outbound_destinations": [
    "api.stripe.com",
    "api.openai.com"
  ],
  "detected_requirements": [
    "openai>=1.0",
    "requests"
  ],
  "entry_point": "agent.py",
  "system_prompt_suggestion": "You are a payment data analyst that summarizes charge information."
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Analysis ID (use to retrieve cached result) |
| `tools` | object[] | Detected external tool/API calls |
| `model_providers` | object[] | Detected LLM provider and model usage |
| `model_usages` | object[] | Detailed model usage with role, variable, file, and line |
| `secrets` | object[] | Detected hardcoded secrets and API keys |
| `outbound_destinations` | string[] | All external hostnames the code connects to |
| `detected_requirements` | string[] | Python package dependencies |
| `entry_point` | string | Detected entry point file |
| `system_prompt_suggestion` | string | AI-generated system prompt suggestion based on the code |

### Tool Detection

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Derived tool name |
| `base_url` | string | Detected base URL |
| `file` | string | Source file |
| `line` | integer | Line number |

### Model Usage Detection

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | Model role: `default`, `chat`, `embedding`, `classify`, `reranking` |
| `variable_name` | string | Variable name in code |
| `file` | string | Source file |
| `line` | integer | Line number |

### Secret Detection

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Secret type (e.g., `api_key`, `oauth_token`, `private_key`) |
| `file` | string | Source file |
| `line` | integer | Line number |
| `severity` | string | `high`, `medium`, or `low` |

!!! warning "Secret detection"
    The analyzer detects hardcoded secrets using pattern matching and Shannon entropy analysis (threshold >= 4.5). Detected secrets are flagged but their values are never stored or logged. **Remove hardcoded secrets before deploying** -- RunAgents injects credentials at runtime.

---

## Retrieve Cached Analysis

<span class="method-get">GET</span> <span class="endpoint">/analysis/:id</span>

Retrieve a previously computed analysis result. Results are cached for 1 hour.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Analysis ID from the analyze response |

=== "curl"

    ```bash
    curl https://api.runagents.io/analysis/analysis-a1b2c3d4 \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response (200 OK)

Returns the same analysis result object as the POST response.

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `analysis not found` | Analysis has expired or does not exist |

---

## Detect Requirements

<span class="method-post">POST</span> <span class="endpoint">/requirements</span>

Detect Python package requirements and entry point from source files. This is a lightweight endpoint that skips full analysis.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | object | Yes | Map of filename to source code content |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/requirements \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "files": {
          "agent.py": "from langchain.chat_models import ChatOpenAI\nfrom langchain.agents import initialize_agent\nimport requests\n",
          "utils.py": "import pandas as pd\nimport numpy as np\n"
        }
      }'
    ```

### Response (200 OK)

```json
{
  "requirements": [
    "langchain",
    "openai>=1.0",
    "requests",
    "pandas",
    "numpy"
  ],
  "entry_point": "agent.py"
}
```

---

## Detected Frameworks

The ingestion engine detects 9+ SDK frameworks and adapts its analysis accordingly:

| Framework | Detection | What is Extracted |
|-----------|-----------|-------------------|
| **LangChain** | `from langchain` imports | Model providers, tools, chain structure |
| **LangGraph** | `from langgraph` imports | Graph nodes, state schema, tool bindings |
| **OpenAI** | `import openai` or `from openai` | Model names, function calling, embeddings |
| **Anthropic** | `import anthropic` | Model names, tool use |
| **Stripe** | `import stripe` or Stripe URLs | API endpoints, key usage |
| **AWS (boto3)** | `import boto3` | Service calls, regions |
| **Google APIs** | Google API client imports | Scopes, service endpoints |
| **Requests/httpx** | `import requests` / `import httpx` | Outbound URLs, auth patterns |
| **FastAPI/Flask** | Framework imports | Endpoints, middleware |

### Two-Layer Analysis

1. **Base layer** (always runs): AST parsing + regex pattern matching. Detects imports, URLs, API keys, and framework-specific patterns.
2. **LLM enrichment** (optional): When enabled, uses an LLM to provide deeper analysis -- understanding intent, suggesting system prompts, and identifying non-obvious tool usage.

!!! info "Analysis accuracy"
    The base layer is deterministic and fast. LLM enrichment improves accuracy for complex codebases with dynamic URL construction or indirect API usage. Both layers are combined in the final result.
