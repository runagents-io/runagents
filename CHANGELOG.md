# Changelog

All notable changes to the public RunAgents CLI and docs surface are documented here.

## v1.2.0 - 2026-04-09

### Added

- `runagents catalog` for listing, inspecting, initializing, and deploying catalog agents such as the Google Workspace assistant
- `runagents policies` for listing, applying, translating, and deleting policy resources
- `runagents approval-connectors` for managing approval delivery integrations, defaults, tests, and activity
- `runagents identity-providers` for managing end-user identity providers used by authenticated agent ingress
- richer `runagents runs` workflows including timeline, wait, export, and improved event summaries

### Improved

- `runagents approvals approve` now supports scoped approval decisions for `once`, `run`, and time-window flows
- `runagents deploy` now supports policy bindings, identity providers, deploy drafts, workflow artifacts, and source-build metadata from the terminal
- `runagents context export` now includes governance and identity resources needed by external assistants, including policies, identity providers, and approval connectors
- public docs, `llms.txt`, and `llms-full.txt` now reflect the mature CLI governance-and-operations workflow

## v1.1.2 - 2026-04-09

### Fixed

- corrected the CLI deploy payload to use `agent_name`, aligning `runagents deploy` with the published Deploy API contract
