#!/usr/bin/env python3
"""Synchronize repo package versions to a single release number."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "release" / "version.json"


def _read_version() -> str:
    data = json.loads(VERSION_FILE.read_text())
    version = str(data["version"]).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Invalid semantic version in {VERSION_FILE}: {version!r}")
    return version


def _write_version(version: str) -> None:
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(json.dumps({"version": version}, indent=2) + "\n")


def _replace_regex(path: Path, pattern: str, replacement: str, expected_count: int | None = 1) -> None:
    original = path.read_text()
    updated, count = re.subn(pattern, replacement, original, flags=re.MULTILINE)
    if expected_count is None:
        if count < 1:
            raise RuntimeError(f"Expected at least one replacement in {path}, got {count}")
    elif count != expected_count:
        raise RuntimeError(f"Expected {expected_count} replacement(s) in {path}, got {count}")
    path.write_text(updated)


def _sync_package_json(path: Path, version: str) -> None:
    data = json.loads(path.read_text())
    data["version"] = version
    data["binaryVersion"] = version
    path.write_text(json.dumps(data, indent=2) + "\n")


def _sync_requirements_template(path: Path, version: str) -> None:
    path.write_text(f"runagents>={version}\n")


def sync(version: str) -> None:
    _write_version(version)
    _sync_package_json(REPO_ROOT / "cli" / "npm" / "package.json", version)
    _replace_regex(
        REPO_ROOT / "sdk" / "python" / "pyproject.toml",
        r'^version = ".*"$',
        f'version = "{version}"',
    )
    _replace_regex(
        REPO_ROOT / "sdk" / "python" / "runagents" / "__init__.py",
        r'^__version__ = ".*"$',
        f'__version__ = "{version}"',
    )
    _replace_regex(
        REPO_ROOT / "sdk" / "python" / "runagents" / "cli" / "binary.py",
        r'^CLI_VERSION = ".*"$',
        f'CLI_VERSION = "{version}"',
    )
    _sync_requirements_template(
        REPO_ROOT / "sdk" / "python" / "runagents" / "cli" / "templates" / "requirements.txt.tmpl",
        version,
    )
    _replace_regex(
        REPO_ROOT / "docs-site" / "docs" / "llms.txt",
        r'^- \[PyPI\]\(https://pypi\.org/project/runagents/\): v.*$',
        f"- [PyPI](https://pypi.org/project/runagents/): v{version}",
    )
    _replace_regex(
        REPO_ROOT / "docs-site" / "docs" / "llms-full.txt",
        r'^PyPI: https://pypi\.org/project/runagents/ \(v.*\)$',
        f"PyPI: https://pypi.org/project/runagents/ (v{version})",
    )
    _replace_regex(
        REPO_ROOT / "docs-site" / "docs" / "sdk" / "index.md",
        r'^- Current repo version: `.*`$',
        f"- Current repo version: `{version}`",
    )
    for path in [
        REPO_ROOT / "docs-site" / "docs" / "sdk" / "index.md",
        REPO_ROOT / "docs-site" / "docs" / "api" / "deploy.md",
        REPO_ROOT / "docs-site" / "docs" / "whats-new" / "releases" / "2026-04-09-scoped-approvals-console-messaging.md",
        REPO_ROOT / "examples" / "product-assistant" / "deploy.py",
        REPO_ROOT / "cli" / "internal" / "commands" / "deploy_test.go",
    ]:
        _replace_regex(
            path,
            r'runagents>=\d+\.\d+\.\d+\\n',
            f"runagents>={version}\\\\n",
            expected_count=None,
        )
    for path in [
        REPO_ROOT / "examples" / "langchain-enterprise" / "requirements.txt",
        REPO_ROOT / "examples" / "multi-agent-local" / "requirements.txt",
        REPO_ROOT / "examples" / "product-assistant" / "requirements.txt",
    ]:
        _replace_regex(
            path,
            r'runagents>=\d+\.\d+\.\d+',
            f"runagents>={version}",
        )


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("usage: sync_release_versions.py [version]", file=sys.stderr)
        return 2
    version = argv[1] if len(argv) == 2 else _read_version()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print(f"invalid semantic version: {version}", file=sys.stderr)
        return 2
    sync(version)
    print(f"Synchronized release version to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
