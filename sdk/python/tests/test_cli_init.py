"""Tests for runagents.cli.init_cmd."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runagents.cli.init_cmd import run_init


class TestRunInit(unittest.TestCase):
    def test_creates_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("runagents.cli.init_cmd.Path.cwd", return_value=Path(tmpdir)):
                run_init(["test-agent"])

            project = Path(tmpdir) / "test-agent"
            self.assertTrue(project.exists())
            self.assertTrue((project / "agent.py").exists())
            self.assertTrue((project / "runagents.yaml").exists())
            self.assertTrue((project / "requirements.txt").exists())
            self.assertTrue((project / "CLAUDE.md").exists())
            self.assertTrue((project / ".cursorrules").exists())
            self.assertTrue((project / "AGENTS.md").exists())
            self.assertTrue((project / ".mcp.json").exists())
            self.assertTrue((project / ".gitignore").exists())

    def test_template_substitution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("runagents.cli.init_cmd.Path.cwd", return_value=Path(tmpdir)):
                run_init(["my-cool-agent"])

            project = Path(tmpdir) / "my-cool-agent"
            yaml_content = (project / "runagents.yaml").read_text()
            self.assertIn("my-cool-agent", yaml_content)

    def test_existing_dir_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "existing").mkdir()
            with mock.patch("runagents.cli.init_cmd.Path.cwd", return_value=Path(tmpdir)):
                with self.assertRaises(SystemExit):
                    run_init(["existing"])


if __name__ == "__main__":
    unittest.main()
