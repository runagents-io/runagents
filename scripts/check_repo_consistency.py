#!/usr/bin/env python3
"""Validate repo-wide product consistency checks."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_LINK_PAGES = (
    "agents",
    "approval-connectors",
    "approvals",
    "billing",
    "build",
    "catalog",
    "deploy",
    "identity-providers",
    "ingestion",
    "model-providers",
    "policies",
    "runs",
    "tools",
)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _read_text(path: Path) -> str:
    return path.read_text()


def _read_version() -> str:
    data = json.loads((REPO_ROOT / "release" / "version.json").read_text())
    version = str(data["version"]).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Invalid semantic version in release/version.json: {version!r}")
    return version


def _expect_regex(errors: list[str], path: Path, pattern: str, expected: str) -> None:
    text = _read_text(path)
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        _fail(errors, f"{path}: pattern not found: {pattern}")
        return
    actual = match.group(1)
    if actual != expected:
        _fail(errors, f"{path}: expected {expected!r}, found {actual!r}")


def _expect_contains(errors: list[str], path: Path, needle: str) -> None:
    text = _read_text(path)
    if needle not in text:
        _fail(errors, f"{path}: missing expected text {needle!r}")


def _check_release_sync(errors: list[str], version: str) -> None:
    package_json = json.loads((REPO_ROOT / "cli" / "npm" / "package.json").read_text())
    if package_json.get("version") != version:
        _fail(errors, "cli/npm/package.json: version does not match release/version.json")
    if package_json.get("binaryVersion") != version:
        _fail(errors, "cli/npm/package.json: binaryVersion does not match release/version.json")

    _expect_regex(errors, REPO_ROOT / "sdk" / "python" / "pyproject.toml", r'^version = "(.*)"$', version)
    _expect_regex(errors, REPO_ROOT / "sdk" / "python" / "runagents" / "__init__.py", r'^__version__ = "(.*)"$', version)
    _expect_regex(errors, REPO_ROOT / "sdk" / "python" / "runagents" / "cli" / "binary.py", r'^CLI_VERSION = "(.*)"$', version)
    _expect_regex(errors, REPO_ROOT / "docs-site" / "docs" / "sdk" / "index.md", r"^- Current repo version: `(.*)`$", version)
    _expect_regex(errors, REPO_ROOT / "docs-site" / "docs" / "cli" / "installation.md", r"^Current version: \*\*(.*)\*\*$", version)
    _expect_regex(errors, REPO_ROOT / "docs-site" / "docs" / "cli" / "installation.md", r"^runagents version (.*)$", version)
    _expect_regex(errors, REPO_ROOT / "docs-site" / "docs" / "llms.txt", r"^- \[PyPI\]\(https://pypi\.org/project/runagents/\): v(.*)$", version)
    _expect_regex(errors, REPO_ROOT / "docs-site" / "docs" / "llms-full.txt", r"^PyPI: https://pypi\.org/project/runagents/ \(v(.*)\)$", version)


def _check_docs_and_distribution(errors: list[str]) -> None:
    _expect_contains(errors, REPO_ROOT / "README.md", "pip install runagents[mcp]")
    _expect_contains(errors, REPO_ROOT / "sdk" / "python" / "README.md", "pip install runagents[mcp]")
    _expect_contains(errors, REPO_ROOT / "docs-site" / "docs" / "cli" / "ai-assistant-setup.md", "pip install runagents[mcp]")


def _check_contract_artifacts(errors: list[str]) -> None:
    openapi_file = REPO_ROOT / "openapi" / "openapi.yaml"
    docs_copy = REPO_ROOT / "docs-site" / "docs" / "api" / "openapi.yaml"
    if not openapi_file.exists():
        _fail(errors, "openapi/openapi.yaml: file does not exist")
    else:
        _expect_contains(errors, openapi_file, "openapi: 3.1.0")
        _expect_contains(errors, openapi_file, "/governance/requests:")
        _expect_contains(errors, openapi_file, "/runs:")
        _expect_contains(errors, openapi_file, "/api/catalog:")
        _expect_contains(errors, openapi_file, "/api/deploy:")
        _expect_contains(errors, openapi_file, "/api/policies:")
        _expect_contains(errors, openapi_file, "/api/settings/approval-connectors:")
        _expect_contains(errors, openapi_file, "/api/identity-providers:")
        _expect_contains(errors, openapi_file, "/api/agents:")
        _expect_contains(errors, openapi_file, "/api/tools:")
        _expect_contains(errors, openapi_file, "/api/model-providers:")
        _expect_contains(errors, openapi_file, "/v1/chat/completions:")
        _expect_contains(errors, openapi_file, "/api/builds:")
        _expect_contains(errors, openapi_file, "/api/billing:")
        _expect_contains(errors, openapi_file, "/analyze:")
        _expect_contains(errors, openapi_file, "/requirements:")
    if not docs_copy.exists():
        _fail(errors, "docs-site/docs/api/openapi.yaml: mirrored docs spec is missing")
    elif openapi_file.read_text() != docs_copy.read_text():
        _fail(errors, "docs-site/docs/api/openapi.yaml: mirrored docs spec is out of sync with openapi/openapi.yaml")

    api_overview = REPO_ROOT / "docs-site" / "docs" / "api" / "overview.md"
    _expect_contains(errors, api_overview, "openapi/openapi.yaml")
    _expect_contains(errors, REPO_ROOT / "docs-site" / "docs" / "api" / "redoc.md", 'data-spec-url="../openapi.yaml"')
    _expect_contains(errors, REPO_ROOT / "docs-site" / "docs" / "api" / "swagger.md", 'data-spec-url="../openapi.yaml"')
    for slug in API_LINK_PAGES:
        page = REPO_ROOT / "docs-site" / "docs" / "api" / f"{slug}.md"
        include = f'--8<-- "api-links/{slug}.md"'
        _expect_contains(errors, page, include)


def main() -> int:
    errors: list[str] = []
    version = _read_version()
    _check_release_sync(errors, version)
    _check_docs_and_distribution(errors)
    _check_contract_artifacts(errors)

    if errors:
        print("Repo consistency check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Repo consistency check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
