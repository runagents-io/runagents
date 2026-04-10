# Approval Workflows

RunAgents approvals are policy-driven. When a governed tool call requires a human decision, the platform creates an approval request and pauses the relevant run.

## SDK surface

```python
requests = client.approvals.list()

client.approvals.approve("req-abc123")
client.approvals.approve("req-abc123", scope="once")
client.approvals.approve("req-abc123", scope="run")
client.approvals.approve("req-abc123", scope="window", duration="4h")
client.approvals.reject("req-abc123")
```

## Approval scopes

- `once`: approve one blocked action
- `run`: approve the current run
- `window`: approve a short-lived user-agent-tool window

The SDK normalizes `window` to the platform scope `agent_user_ttl`.

## Data model

The SDK returns typed `ApprovalRequest` objects so approval flows can be inspected programmatically without raw dict parsing.

See [Approval Types](api/approvals.md).
