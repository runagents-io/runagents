# Build API

The Build API generates container images from agent source code. It automatically detects the language, generates a Dockerfile, installs dependencies, and builds the image. For most users, the [Deploy API](deploy.md) handles builds automatically -- use the Build API directly only for custom build workflows.

---

## Start a Build

<span class="method-post">POST</span> <span class="endpoint">/api/builds</span>

Start an asynchronous build from source files. Returns immediately with a build ID and the deterministic image URI.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Agent name (used to derive the image name) |
| `files` | object | Yes | Map of filename to source code content |
| `entry_point` | string | No | Entry point file (auto-detected if not specified) |
| `requirements` | string | No | Python requirements in pip format |
| `framework` | string | No | Agent framework hint (e.g., `langchain`, `openai`) |

=== "curl"

    ```bash
    curl -X POST https://api.runagents.io/api/builds \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "my-agent",
        "files": {
          "agent.py": "from openai import OpenAI\nimport requests\n\nclient = OpenAI()\n\ndef main():\n    response = client.chat.completions.create(\n        model=\"gpt-4o-mini\",\n        messages=[{\"role\": \"user\", \"content\": \"Hello\"}]\n    )\n    print(response.choices[0].message.content)\n\nif __name__ == \"__main__\":\n    main()\n",
          "requirements.txt": "openai>=1.0\nrequests"
        },
        "entry_point": "agent.py"
      }'
    ```

=== "Python"

    ```python
    import requests
    import time

    # Start the build
    resp = requests.post(
        "https://api.runagents.io/api/builds",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "name": "my-agent",
            "files": {
                "agent.py": open("agent.py").read(),
                "requirements.txt": open("requirements.txt").read(),
            },
            "entry_point": "agent.py",
        },
    )
    build = resp.json()
    build_id = build["id"]
    print(f"Build started: {build_id}")
    print(f"Image will be: {build['image']}")

    # Poll for completion
    while True:
        status = requests.get(
            f"https://api.runagents.io/api/builds/{build_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        ).json()

        print(f"Status: {status['status']}")
        if status["status"] in ("SUCCEEDED", "FAILED"):
            break
        time.sleep(5)
    ```

### Response (202 Accepted)

```json
{
  "id": "build-a1b2c3d4",
  "status": "PENDING",
  "image": "registry.runagents.io/my-agent:a1b2c3d4",
  "created_at": "2026-02-23T10:00:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Build ID for polling status |
| `status` | string | Initial status: `PENDING` |
| `image` | string | Deterministic image URI (available before build completes) |
| `created_at` | string | ISO 8601 build start timestamp |

!!! info "Deterministic image URI"
    The image URI is returned immediately in the `202` response, before the build completes. This allows the [Deploy API](deploy.md) to create the agent with the image reference right away while the build runs asynchronously.

---

## Get Build Status

<span class="method-get">GET</span> <span class="endpoint">/api/builds/:id</span>

Poll the status of a build.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Build ID |

=== "curl"

    ```bash
    curl https://api.runagents.io/api/builds/build-a1b2c3d4 \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY"
    ```

### Response: Build in progress (200 OK)

```json
{
  "id": "build-a1b2c3d4",
  "status": "BUILDING",
  "image": "registry.runagents.io/my-agent:a1b2c3d4",
  "created_at": "2026-02-23T10:00:00Z"
}
```

### Response: Build succeeded (200 OK)

```json
{
  "id": "build-a1b2c3d4",
  "status": "SUCCEEDED",
  "image": "registry.runagents.io/my-agent:a1b2c3d4",
  "created_at": "2026-02-23T10:00:00Z",
  "completed_at": "2026-02-23T10:02:30Z"
}
```

### Response: Build failed (200 OK)

```json
{
  "id": "build-a1b2c3d4",
  "status": "FAILED",
  "image": "registry.runagents.io/my-agent:a1b2c3d4",
  "error": "pip install failed: no matching distribution found for nonexistent-package",
  "created_at": "2026-02-23T10:00:00Z",
  "completed_at": "2026-02-23T10:01:15Z"
}
```

### Errors

| Status | Error | Description |
|--------|-------|-------------|
| `404` | `build not found` | Build ID does not exist |

---

## Build Statuses

| Status | Description |
|--------|-------------|
| `PENDING` | Build queued, waiting to start |
| `BUILDING` | Build is in progress |
| `SUCCEEDED` | Build completed, image pushed to registry |
| `FAILED` | Build failed (check `error` field for details) |

```
PENDING --> BUILDING --> SUCCEEDED
                    --> FAILED
```

---

## How Builds Work

The build service performs the following steps:

1. **Dockerfile generation** -- Detects the language and framework, then generates an optimized Dockerfile. For Python agents, it maps imports to pip packages (e.g., `import openai` becomes `openai>=1.0` in requirements).

2. **Artifact upload** -- Uploads source files and the generated Dockerfile to the platform's artifact storage.

3. **Container build** -- Builds the container image in an isolated environment.

4. **Registry push** -- Pushes the built image to the platform's container registry.

### Generated Dockerfile (example)

For a Python agent with `agent.py` and `requirements.txt`, the generated Dockerfile looks like:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "agent.py"]
```

### Automatic Dependency Detection

When `requirements.txt` is not provided, the build service maps Python imports to packages:

| Import | Package |
|--------|---------|
| `import openai` | `openai>=1.0` |
| `from langchain` | `langchain` |
| `import anthropic` | `anthropic` |
| `import requests` | `requests` |
| `import stripe` | `stripe` |
| `import boto3` | `boto3` |
| `from fastapi` | `fastapi[standard]` |
| `import pandas` | `pandas` |
| `import numpy` | `numpy` |

!!! tip "Providing requirements.txt"
    For production agents, include a `requirements.txt` with pinned versions rather than relying on automatic detection. This ensures reproducible builds.

---

## Using Builds with Deploy

For most workflows, you do not need to call the Build API directly. The [Deploy API](deploy.md) triggers builds automatically when you provide `source_files` without an `image`:

=== "curl"

    ```bash
    # This automatically triggers a build + deploy
    curl -X POST https://api.runagents.io/api/deploy \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "agent_name": "my-agent",
        "source_files": {
          "agent.py": "...",
          "requirements.txt": "openai>=1.0"
        },
        "entry_point": "agent.py",
        "llm_configs": [{"provider": "openai", "model": "gpt-4o-mini"}]
      }'
    ```

The Deploy API returns the `build_id` so you can track the build status separately if needed.
