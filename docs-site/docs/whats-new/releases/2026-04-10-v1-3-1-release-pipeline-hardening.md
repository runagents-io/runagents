# RunAgents v1.3.1: Release Pipeline Hardening

RunAgents `v1.3.1` is a patch release focused on release reliability for the newly expanded public SDK and MCP surface.

## What changed

- PyPI publishing now uses Trusted Publishing from GitHub Actions instead of a long-lived API token
- the release workflow is explicitly bound to the `pypi` GitHub environment for safer publication
- the public release line stays aligned across CLI, SDK, MCP, docs, npm, Homebrew, and S3 installs

## Why this release exists

`v1.3.0` introduced a much broader public Python SDK and MCP surface, but the PyPI publish path still depended on a missing GitHub secret.

`v1.3.1` fixes that release-engineering gap so future releases can publish the Python package automatically and consistently.

## Impact

This release does not add new SDK, CLI, or MCP features.

It improves the reliability of the release pipeline behind those surfaces.

## Recommended action

Move to `v1.3.1` if you want:

- the latest unified CLI + SDK + MCP release number
- the hardened release workflow for future Python package publishes
- the cleanest baseline for the next feature release
