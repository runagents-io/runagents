# RunAgents v1.4.1: CLI Install Path Fixes

RunAgents `v1.4.1` is a patch release focused on install-path reliability for the published CLI surfaces.

## What changed

- the published npm package now includes the wrapper entrypoint used to create the `runagents` executable on install
- the Python SDK wrapper now ignores its own entrypoint on `PATH` and correctly falls through to the native CLI download path
- the release line now has focused coverage for the Python wrapper resolution path so the same regression is less likely to ship again

## Why this release exists

`v1.4.0` shipped the intended CLI, npm, PyPI, Homebrew, and docs surfaces, but two install paths still had end-user regressions:

- the npm package metadata pointed at `bin/runagents.js`, but that file was missing from the published package
- the Python `runagents` wrapper could resolve back to itself on `PATH` instead of downloading the native CLI binary

`v1.4.1` fixes those two install-path issues without changing the underlying CLI feature set.

## Impact

This release does not add new platform, SDK, or CLI features.

It improves the reliability of:

- `npm install -g @runagents/cli`
- `npx @runagents/cli`
- `pip install runagents`
- first-run Python wrapper bootstrap into the native CLI

Homebrew, direct binary downloads, and the curl installer were already healthy in `v1.4.0`.

## Recommended action

Move to `v1.4.1` if you install RunAgents through npm or PyPI, or if you want the cleanest patch baseline after `v1.4.0`.

If you already installed through Homebrew or the direct curl installer, this patch does not require any workflow changes, but it keeps the full public install surface aligned on one release number.
