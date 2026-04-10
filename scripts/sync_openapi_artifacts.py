#!/usr/bin/env python3
"""Synchronize publishable OpenAPI docs artifacts from the canonical spec."""

from __future__ import annotations

import argparse
import re
import sys
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "openapi" / "openapi.yaml"
DOCS_API_DIR = REPO_ROOT / "docs-site" / "docs" / "api"
DOCS_COPY = DOCS_API_DIR / "openapi.yaml"
GENERATED_SPECS_DIR = DOCS_API_DIR / "_generated" / "specs"
GENERATED_LINKS_DIR = REPO_ROOT / "docs-site" / "includes" / "api-links"

PAGE_CONFIG: dict[str, dict[str, str | None]] = {
    "agents": {"title": "Agents API", "tag": "Agents"},
    "approval-connectors": {"title": "Approval Connectors API", "tag": "Approval Connectors"},
    "approvals": {"title": "Approvals API", "tag": "Approvals"},
    "billing": {"title": "Billing API", "tag": "Billing"},
    "build": {"title": "Build API", "tag": "Builds"},
    "catalog": {"title": "Catalog API", "tag": "Catalog"},
    "deploy": {"title": "Deploy API", "tag": "Deploy"},
    "identity-providers": {"title": "Identity Providers API", "tag": "Identity Providers"},
    "ingestion": {"title": "Ingestion API", "tag": "Ingestion"},
    "model-providers": {"title": "Model Providers API", "tag": "Model Providers"},
    "policies": {"title": "Policies API", "tag": "Policies"},
    "runs": {"title": "Runs API", "tag": "Runs"},
    "tools": {"title": "Tools API", "tag": "Tools"},
}


def _load_spec() -> dict:
    return yaml.safe_load(SOURCE.read_text())


def _dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def _iter_tag_operations(spec: dict, tag: str) -> list[tuple[str, str, dict]]:
    operations: list[tuple[str, str, dict]] = []
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            if tag in operation.get("tags", []):
                operations.append((method.upper(), path, operation))
    return operations


def _camel_token(value: str) -> str:
    words = re.split(r"[^A-Za-z0-9]+", value)
    return "".join(word[:1].upper() + word[1:] for word in words if word)


def _generated_operation_id(method: str, path: str) -> str:
    parts = [method.lower()]
    for segment in path.strip("/").split("/"):
        if not segment:
            continue
        if segment.startswith("{") and segment.endswith("}"):
            parts.append("By" + _camel_token(segment[1:-1]))
        else:
            parts.append(_camel_token(segment))
    return "".join(parts)


def _spec_for_generated_views(spec: dict) -> dict:
    enriched = deepcopy(spec)
    for path, path_item in enriched.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            operation.setdefault("operationId", _generated_operation_id(method, path))
    return enriched


def _filtered_spec(spec: dict, tag: str) -> dict:
    filtered = deepcopy(spec)
    filtered["tags"] = [item for item in spec.get("tags", []) if item.get("name") == tag]
    filtered_paths: dict[str, dict] = {}
    for method, path, operation in _iter_tag_operations(spec, tag):
        path_item = filtered_paths.setdefault(path, {})
        path_item[method.lower()] = deepcopy(operation)
    filtered["paths"] = filtered_paths
    return filtered


def _snippet_for_page(slug: str, spec: dict, tag: str | None, title: str) -> str:
    if not tag:
        return (
            '!!! info "Generated Reference Views"\n'
            "    OpenAPI-generated reference views are not published for this endpoint group yet.\n"
            '    Use the shared [OpenAPI contract](../openapi/) and the broad [Redoc](../redoc/) or [Swagger UI](../swagger/) views in the meantime.\n'
        )

    operations = _iter_tag_operations(spec, tag)
    if not operations:
        return (
            '!!! warning "Generated Reference Views"\n'
            f"    Expected operations for the `{tag}` tag were not found in the canonical OpenAPI contract.\n"
        )

    spec_href = f"../_generated/specs/{slug}.yaml"
    redoc_href = f"../redoc/?spec=../_generated/specs/{slug}.yaml"
    swagger_href = f"../swagger/?spec=../_generated/specs/{slug}.yaml"
    rows = []
    for method, path, operation in operations:
        operation_id = operation["operationId"]
        redoc_operation_href = f"{redoc_href}#operation/{quote(operation_id)}"
        swagger_operation_href = f"{swagger_href}#/{quote(tag)}/{quote(operation_id)}"
        rows.append(
            f"    | `{method} {path}` | [Redoc]({redoc_operation_href}) | [Swagger]({swagger_operation_href}) |\n"
        )
    return (
        '!!! info "Generated Reference Views"\n'
        f"    - [Filtered OpenAPI YAML]({spec_href})\n"
        f"    - [Redoc for {title}]({redoc_href})\n"
        f"    - [Swagger UI for {title}]({swagger_href})\n"
        "\n"
        "    | Operation | Redoc | Swagger |\n"
        "    | --- | --- | --- |\n"
        + "".join(rows)
    )


def sync() -> int:
    spec = _load_spec()
    view_spec = _spec_for_generated_views(spec)
    DOCS_API_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_SPECS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_LINKS_DIR.mkdir(parents=True, exist_ok=True)

    DOCS_COPY.write_text(SOURCE.read_text())

    for slug, config in PAGE_CONFIG.items():
        title = str(config["title"])
        tag = config["tag"]
        if tag:
            (GENERATED_SPECS_DIR / f"{slug}.yaml").write_text(_dump_yaml(_filtered_spec(view_spec, str(tag))))
        elif (GENERATED_SPECS_DIR / f"{slug}.yaml").exists():
            (GENERATED_SPECS_DIR / f"{slug}.yaml").unlink()
        (GENERATED_LINKS_DIR / f"{slug}.md").write_text(_snippet_for_page(slug, view_spec, tag, title))

    print("Synchronized OpenAPI docs artifacts")
    return 0


def check() -> int:
    expected_spec = SOURCE.read_text()
    if not DOCS_COPY.exists():
        print(f"Missing mirrored docs spec: {DOCS_COPY}", file=sys.stderr)
        return 1
    if DOCS_COPY.read_text() != expected_spec:
        print(
            "OpenAPI docs artifact is out of sync. Run `python scripts/sync_openapi_artifacts.py`.",
            file=sys.stderr,
        )
        return 1

    spec = _load_spec()
    view_spec = _spec_for_generated_views(spec)
    for slug, config in PAGE_CONFIG.items():
        title = str(config["title"])
        tag = config["tag"]
        link_file = GENERATED_LINKS_DIR / f"{slug}.md"
        expected_link = _snippet_for_page(slug, view_spec, tag, title)
        if not link_file.exists():
            print(f"Missing generated link snippet: {link_file}", file=sys.stderr)
            return 1
        if link_file.read_text() != expected_link:
            print(f"Generated link snippet out of sync: {link_file}", file=sys.stderr)
            return 1

        spec_file = GENERATED_SPECS_DIR / f"{slug}.yaml"
        if tag:
            expected_filtered = _dump_yaml(_filtered_spec(view_spec, str(tag)))
            if not spec_file.exists():
                print(f"Missing generated filtered spec: {spec_file}", file=sys.stderr)
                return 1
            if spec_file.read_text() != expected_filtered:
                print(f"Generated filtered spec out of sync: {spec_file}", file=sys.stderr)
                return 1
        elif spec_file.exists():
            print(f"Unexpected generated filtered spec for uncovered page: {spec_file}", file=sys.stderr)
            return 1

    print("OpenAPI docs artifacts are synchronized")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if docs artifacts are out of sync")
    args = parser.parse_args(argv[1:])
    return check() if args.check else sync()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
