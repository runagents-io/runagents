"""``runagents init [name]`` — scaffold a new agent project."""

import os
import sys
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def run_init(args: list[str]) -> None:
    if args and args[0] in ("-h", "--help"):
        print("Usage: runagents init [name]\n\nScaffold a new agent project.")
        return

    name = args[0] if args else "my-agent"
    target = Path.cwd() / name

    if target.exists():
        print(f"Error: directory '{name}' already exists.", file=sys.stderr)
        sys.exit(1)

    target.mkdir(parents=True)
    _render_templates(target, name)

    print(f"Created project '{name}/' with:")
    for f in sorted(target.rglob("*")):
        if f.is_file():
            print(f"  {f.relative_to(target)}")
    print(f"\nNext steps:\n  cd {name}\n  pip install runagents\n  runagents dev")


def _render_templates(target: Path, name: str) -> None:
    """Read .tmpl files and write rendered output."""
    replacements = {
        "{{name}}": name,
        "{{name_underscore}}": name.replace("-", "_"),
    }

    file_map = {
        "agent.py.tmpl": "agent.py",
        "runagents.yaml.tmpl": "runagents.yaml",
        "requirements.txt.tmpl": "requirements.txt",
        "claude_md.tmpl": "CLAUDE.md",
        "cursorrules.tmpl": ".cursorrules",
        "agents_md.tmpl": "AGENTS.md",
        "mcp_json.tmpl": ".mcp.json",
        "gitignore.tmpl": ".gitignore",
    }

    for tmpl_name, out_name in file_map.items():
        tmpl_path = _TEMPLATE_DIR / tmpl_name
        if not tmpl_path.exists():
            continue
        content = tmpl_path.read_text()
        for old, new in replacements.items():
            content = content.replace(old, new)
        (target / out_name).write_text(content)
