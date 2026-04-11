# Platform Approval API

The Python SDK and MCP approval tools are backed by the platform approval endpoints documented on the main docs site.

Primary reference:

- [Approvals API on docs.runagents.io](https://docs.runagents.io/api/approvals/)
- [OpenAPI contract](https://docs.runagents.io/api/openapi/)
- [Redoc reference](https://docs.runagents.io/api/redoc/?spec=_generated/specs/approvals.yaml)
- [Swagger UI](https://docs.runagents.io/api/swagger/?spec=_generated/specs/approvals.yaml)

Relevant endpoints:

- `GET /governance/requests`
- `POST /governance/requests/:id/approve`
- `POST /governance/requests/:id/reject`
