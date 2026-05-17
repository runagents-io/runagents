# RunAgents v1.4.2: Workspace API Key Auth for Public API Clients

RunAgents `v1.4.2` is a patch release focused on the public programmatic API auth surface.

## What changed

- the public OpenAPI contract now models workspace API keys as `X-RunAgents-API-Key`
- Swagger UI now prompts for the workspace API-key header instead of bearer auth for `ra_ws_` keys
- generated API docs and filtered OpenAPI specs now use the same workspace API-key scheme
- the Python SDK and Go CLI now send `ra_ws_` workspace keys through `X-RunAgents-API-Key`
- non-workspace tokens continue to use `Authorization: Bearer` for connected OIDC/JWT flows
- example deploy scripts no longer print configured API keys into generated curl commands
- repo consistency checks now detect bundled external asset hosts through parsed URL hostnames instead of raw substring matching

## Why this release exists

Hosted trial and company URLs reserve `Authorization: Bearer` for connected identity-provider JWT flows.

Workspace API keys use the `ra_ws_` prefix and are not JWTs. When Swagger UI sent those keys as bearer tokens, hosted ingress could reject the request before it reached the governance API.

`v1.4.2` aligns the public contract, docs, SDK, CLI, and examples with the intended split:

- workspace admin/programmatic access: `X-RunAgents-API-Key`
- connected end-user or approval identity flows: `Authorization: Bearer`

## Impact

This release improves:

- Swagger UI requests from `docs.runagents.io`
- direct curl calls copied from the API docs
- Python SDK calls made with `ra_ws_` workspace keys
- Go CLI calls made with `ra_ws_` workspace keys
- generated or assistant-assisted API usage based on the public OpenAPI contract

This release does not change the control-plane authorization model itself. It makes the public clients send workspace keys through the header the hosted API expects.

## Recommended action

Move to `v1.4.2` if you use:

- Swagger UI against a trial or company workspace URL
- the Python SDK with a workspace API key
- the Go CLI with a workspace API key
- generated clients based on the public OpenAPI contract

If you call the API directly, send workspace keys like this:

```bash
curl -X GET "https://YOUR_TRIAL.try.runagents.io/api/v1/policies" \
  -H "X-RunAgents-API-Key: ra_ws_..."
```

Do not send `ra_ws_` workspace keys as `Authorization: Bearer` tokens.

## Learn more

- [API Overview](../../api/overview.md)
- [API Quickstart](../../getting-started/api-quickstart.md)
- [Swagger UI](../../api/swagger.md)
- [CLI Installation](../../cli/installation.md)
- [Python SDK](../../sdk/index.md)
