# MCP Tools

## Core families

| Family | Representative tools |
|--------|-----------------------|
| Workspace | `list_agents`, `get_agent`, `list_tools`, `list_models` |
| Runs | `list_runs`, `get_run`, `get_run_events`, `get_run_timeline`, `wait_for_run`, `export_run` |
| Catalog | `list_catalog_agents`, `get_catalog_agent`, `list_catalog_versions`, `deploy_catalog_agent` |
| Policies | `list_policies`, `get_policy`, `apply_policy`, `delete_policy`, `translate_policy` |
| Approval connectors | `list_approval_connectors`, `get_approval_connector`, `apply_approval_connector`, `delete_approval_connector`, `test_approval_connector`, `get_approval_connector_defaults`, `set_approval_connector_defaults`, `list_approval_connector_activity` |
| Identity providers | `list_identity_providers`, `get_identity_provider`, `apply_identity_provider`, `delete_identity_provider` |
| Approvals | `approve_request`, `reject_request` |

## Approval tools

Use approval tools when the assistant is helping an operator resolve pending governed writes.

- `approve_request(request_id, scope="", duration="")`
- `reject_request(request_id)`

For scope values, use:

- `once`
- `run`
- `window`
