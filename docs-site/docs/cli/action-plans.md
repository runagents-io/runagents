# Action Plans

Action plans let external assistants (Codex / Claude Code) generate deterministic changes, while RunAgents validates and applies them safely.

## Plan Schema

Top-level fields:

- `plan_id` (optional string): correlation ID for your workflow.
- `continue_on_error` (optional bool): when `true`, keep applying remaining actions after a failure.
- `actions` (required array): ordered list of actions.

Each action:

- `id` (optional string): human-readable step ID.
- `type` (required string): action type.
- `idempotency_key` (required string): unique per action in a plan.
- `params` (object): action-specific payload.

Canonical JSON Schema and curated examples:

- [Action Plan Schema (`plan-schema.json`)](plan-schema.json)
- [Bootstrap Agent Plan Example](examples/bootstrap-agent-plan.json)
- [Deploy From Draft Example](examples/deploy-from-draft-plan.json)

## Supported Action Types

| Type | Required Params | Purpose |
|------|------------------|---------|
| `tool.upsert` | `name`, `spec.connection.baseUrl` | Create or update a Tool |
| `model_provider.upsert` | `name`, `spec.provider`, `spec.endpoint`, `spec.models` | Create or update a Model Provider |
| `policy.upsert` | `name`, `spec` | Create or update a Policy |
| `deploy_draft.create_or_patch` | optional `id` + draft fields | Create a new deploy draft or patch existing draft |
| `deploy.execute` | `agent_name` + one of `draft_id`/`artifact_id`/`image`/`source_files` | Execute deployment |
| `starter_kit.seed` | none | Seed starter resources |

## Validate a Plan

```bash
runagents action validate --file plan.json
runagents action validate --file plan.json -o json
```

Validation checks:

- required fields
- action-type schema
- duplicate `idempotency_key` values
- plan-level readiness before mutation

## Apply a Plan

```bash
runagents action apply --file plan.json
runagents action apply --file plan.json -o json
```

Apply executes actions in order and returns per-action statuses (`applied`, `failed`, `skipped`, `invalid`).

## Example Plan

```json
{
  "plan_id": "bootstrap-payments-agent",
  "continue_on_error": false,
  "actions": [
    {
      "id": "tool-1",
      "type": "tool.upsert",
      "idempotency_key": "bootstrap.tool.payments.v1",
      "params": {
        "name": "payments-api",
        "spec": {
          "description": "Payments API",
          "connection": {
            "topology": "External",
            "baseUrl": "https://payments.example.com",
            "port": 443,
            "scheme": "HTTPS",
            "authentication": {"type": "None"}
          },
          "governance": {
            "accessControl": {"mode": "Open"}
          }
        }
      }
    },
    {
      "id": "draft-1",
      "type": "deploy_draft.create_or_patch",
      "idempotency_key": "bootstrap.draft.payments.v1",
      "params": {
        "id": "draft-payments-01",
        "step": "connect",
        "source_type": "code",
        "tool_mappings": {"payments": "payments-api"}
      }
    }
  ]
}
```

## Notes

- Keep `idempotency_key` stable for retries of the same intent.
- Use `validate` before `apply` in all CI or assistant-driven flows.
- Prefer `-o json` for machine parsing from external assistants.
