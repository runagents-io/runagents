# Python SDK Overview

The RunAgents Python SDK is the programmatic management surface for:

- agents
- tools
- model providers
- runs and run timelines
- approvals
- catalog deployments
- policies
- approval connectors
- identity providers

## Basic client usage

```python
from runagents import Client

client = Client()

agents = client.agents.list()
runs = client.runs.list(agent="payment-agent", limit=10)
approvals = client.approvals.list()
```

## Approval workflow example

```python
pending = client.approvals.list()

for request in pending:
    print(request.id, request.tool_id, request.status)

client.approvals.approve("req-abc123", scope="run")
client.approvals.reject("req-def456")
```

## Next pages

- [Approval workflows](approvals.md)
- [Client API reference](api/client.md)
- [Approval types](api/approvals.md)
