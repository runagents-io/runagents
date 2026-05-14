# Action Plans API

Validate and apply deterministic action plans over HTTP.

This is the same action-plan workflow used by:

- `runagents action validate`
- `runagents action apply`
- `client.actions.validate(...)`
- `client.actions.apply(...)`
- assistant tools such as `validate_plan` and `apply_plan` in the RunAgents MCP server

Download the OpenAPI fragment:

- [Action Plans OpenAPI (`action-plans-openapi.yaml`)](action-plans-openapi.yaml)

Canonical plan schema and examples:

- [Action Plan Schema (`../cli/plan-schema.json`)](../cli/plan-schema.json)
- [Action Plans CLI guide](../cli/action-plans.md)

---

## Validate A Plan

<span class="method-post">POST</span> <span class="endpoint">/actions/validate</span>

Validates an action plan without mutating resources.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_id` | string | No | Optional correlation id |
| `continue_on_error` | boolean | No | Apply-only flag preserved in the plan payload |
| `actions` | array | Yes | Ordered action list |

Each action includes:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | No | Optional human-readable step id |
| `type` | string | Yes | Action type |
| `idempotency_key` | string | Yes | Stable key for retry safety |
| `params` | object | No | Action-specific payload |

Supported action types:

- `tool.upsert`
- `model_provider.upsert`
- `policy.upsert`
- `deploy_draft.create_or_patch`
- `deploy.execute`
- `starter_kit.seed`

=== "curl"

    ```bash
    curl -X POST https://acme.runagents.io/api/v1/workspaces/revops/actions/validate \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d @plan.json
    ```

=== "Python"

    ```python
    from runagents import Client

    client = Client()
    result = client.actions.validate(plan)
    print(result.valid)
    for item in result.results:
        print(item.id, item.type, item.valid, item.errors)
    ```

### Response (200 OK)

```json
{
  "plan_id": "bootstrap-payments-agent",
  "namespace": "default",
  "valid": true,
  "results": [
    {
      "id": "tool-1",
      "type": "tool.upsert",
      "idempotency_key": "bootstrap.tool.payments.v1",
      "valid": true,
      "resource_ref": "/tools/payments-api"
    }
  ]
}
```

---

## Apply A Plan

<span class="method-post">POST</span> <span class="endpoint">/actions/apply</span>

Validates the plan and, if valid, executes actions in order.

=== "curl"

    ```bash
    curl -X POST https://acme.runagents.io/api/v1/workspaces/revops/actions/apply \
      -H "Authorization: Bearer $RUNAGENTS_API_KEY" \
      -H "Content-Type: application/json" \
      -d @plan.json
    ```

=== "Python"

    ```python
    from runagents import Client

    client = Client()
    result = client.actions.apply(plan)
    print(result.applied, result.applied_count, result.failed_count)
    for item in result.results:
        print(item.id, item.status, item.resource_ref, item.error)
    ```

### Response (200 OK)

```json
{
  "plan_id": "bootstrap-payments-agent",
  "namespace": "default",
  "applied": true,
  "applied_count": 2,
  "failed_count": 0,
  "results": [
    {
      "id": "tool-1",
      "type": "tool.upsert",
      "idempotency_key": "bootstrap.tool.payments.v1",
      "status": "applied",
      "resource_ref": "/tools/payments-api"
    },
    {
      "id": "draft-1",
      "type": "deploy_draft.create_or_patch",
      "idempotency_key": "bootstrap.draft.payments.v1",
      "status": "applied",
      "resource_ref": "/deploy-drafts/draft-payments-01"
    }
  ]
}
```

### Validation Failure (400 Bad Request)

When validation fails before mutation, the API returns an apply-shaped response with per-action `invalid` statuses:

```json
{
  "plan_id": "broken-plan",
  "namespace": "default",
  "applied": false,
  "applied_count": 0,
  "failed_count": 1,
  "results": [
    {
      "id": "tool-1",
      "type": "tool.upsert",
      "idempotency_key": "dup-key",
      "status": "invalid",
      "error": "idempotency_key is required"
    }
  ]
}
```

---

## Notes

- Use `validate` before `apply` in CI and assistant-driven workflows.
- Keep `idempotency_key` stable across safe retries of the same intent.
- The canonical per-action payload rules still live in the [Action Plan Schema](../cli/plan-schema.json).
