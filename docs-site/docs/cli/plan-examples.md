# Action Plan Examples

Use these canonical examples as starting points for Codex/Claude Code action workflows.

## Files

- [Bootstrap Agent Plan](examples/bootstrap-agent-plan.json)
- [Deploy From Draft Plan](examples/deploy-from-draft-plan.json)
- [Schema Reference (`plan-schema.json`)](plan-schema.json)

## Validate

```bash
runagents action validate --file docs-site/docs/cli/examples/bootstrap-agent-plan.json -o json
runagents action validate --file docs-site/docs/cli/examples/deploy-from-draft-plan.json -o json
```

## Apply

```bash
runagents action apply --file docs-site/docs/cli/examples/bootstrap-agent-plan.json -o json
runagents action apply --file docs-site/docs/cli/examples/deploy-from-draft-plan.json -o json
```

## Notes

- Keep each `idempotency_key` stable across retries of the same intent.
- Prefer `validate` in CI and assistant loops before `apply`.
