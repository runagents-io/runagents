#!/usr/bin/env python3
"""Validate released public surface parity against a shipped capability registry."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "release" / "capabilities-public.yaml"


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _read_text(path: Path) -> str:
    return path.read_text()


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"Missing capability registry: {CONFIG_PATH}", file=sys.stderr)
        return 1

    config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    capabilities = config.get("capabilities", {}) or {}
    errors: list[str] = []
    evidence_checks = 0

    for capability_name, capability in capabilities.items():
        surfaces = capability.get("surfaces", {}) or {}
        if not surfaces:
            _fail(errors, f"{capability_name}: no surfaces declared")
            continue
        for surface_name, surface in surfaces.items():
            evidence = surface.get("evidence", []) or []
            if not evidence:
                _fail(errors, f"{capability_name}.{surface_name}: no evidence declared")
                continue
            for item in evidence:
                evidence_checks += 1
                rel_path = item.get("path", "")
                if not rel_path:
                    _fail(errors, f"{capability_name}.{surface_name}: evidence entry missing path")
                    continue
                path = REPO_ROOT / rel_path
                if not path.exists():
                    _fail(errors, f"{capability_name}.{surface_name}: missing file {rel_path}")
                    continue
                needle = item.get("contains")
                if needle is not None:
                    text = _read_text(path)
                    if needle not in text:
                        _fail(
                            errors,
                            f"{capability_name}.{surface_name}: {rel_path} missing expected text {needle!r}",
                        )

    print("Surface parity check")
    print(f"  config: {CONFIG_PATH.relative_to(REPO_ROOT)}")
    print(f"  capabilities: {len(capabilities)}")
    print(f"  evidence checks: {evidence_checks}")

    if errors:
        print("  result: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("  result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
