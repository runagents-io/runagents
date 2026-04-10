from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK_PATH = ROOT / "sdk" / "python"
if str(SDK_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PATH))

project = "RunAgents SDK & MCP Reference"
copyright = "2026, RunAgents"
author = "RunAgents"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
root_doc = "index"

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
napoleon_google_docstring = True
napoleon_numpy_docstring = False

myst_heading_anchors = 3

html_theme = "furo"
html_title = "RunAgents SDK & MCP Reference"
html_static_path: list[str] = []
html_theme_options = {
    "source_repository": "https://github.com/runagents-io/runagents/",
    "source_branch": "main",
    "source_directory": "docs-site/docs-rtd/",
}
