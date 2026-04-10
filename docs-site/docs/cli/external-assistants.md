# External Assistants

Use RunAgents with external assistants (Codex / Claude Code) without relying on built-in RunAgents Copilot.

## 1. Set External Assistant Mode

```bash
runagents config set assistant-mode external
```

This keeps RunAgents as the control plane (validation, governance, deployment), while your external assistant handles reasoning.

## 2. Export Workspace Context

```bash
runagents context export -o json > context.json
```

This snapshot includes:

- agents
- tools
- model providers
- policies
- identity providers
- approval connectors
- approvals
- deploy drafts

Use `--strict` if you want export to fail on any partial error:

```bash
runagents context export --strict -o json > context.json
```

## 3. Ask Assistant to Generate an Action Plan

Prompt your assistant with `context.json` and ask it to create `plan.json` using the Action Plan schema.

Then validate:

```bash
runagents action validate --file plan.json -o json
```

## 4. Apply Plan

```bash
runagents action apply --file plan.json -o json
```

## Add workflow skills when the task is non-trivial

For production work, pair exported context and action plans with the public RunAgents skills library. The skills help assistants reason about catalog deployment, approvals, tooling, debugging, and interfaces such as WhatsApp or Slack with much less prompt churn.

See [RunAgents Skills](skills.md).

## Recommended Loop

1. `context export`
2. assistant generates/updates `plan.json`
3. `action validate`
4. `action apply`
5. `context export` again for confirmation

## Safety Guidelines

- Always run `validate` before `apply`.
- Keep a stable `idempotency_key` per action intent.
- Use `continue_on_error: false` for production deploy sequences.
- Store plan files in version control for auditability.

## Related

- [Action Plans](action-plans.md)
- [Action Plan Examples](plan-examples.md)
- [Action Plan Schema (`plan-schema.json`)](plan-schema.json)
- [CLI Commands](commands.md)
