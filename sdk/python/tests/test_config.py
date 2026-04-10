"""Tests for runagents.config."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runagents.config import Config, load_config, save_config


class TestLoadConfig(unittest.TestCase):
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("runagents.config._CONFIG_FILE", Path("/nonexistent/config.json")):
            cfg = load_config()
        self.assertEqual(cfg.endpoint, "http://localhost:8092")
        self.assertEqual(cfg.api_key, "")
        self.assertEqual(cfg.namespace, "default")
        self.assertEqual(cfg.assistant_mode, "external")

    def test_env_overrides(self):
        env = {
            "RUNAGENTS_ENDPOINT": "https://api.example.com",
            "RUNAGENTS_API_KEY": "sk-test",
            "RUNAGENTS_NAMESPACE": "prod",
            "RUNAGENTS_ASSISTANT_MODE": "runagents",
        }
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch("runagents.config._CONFIG_FILE", Path("/nonexistent/config.json")):
            cfg = load_config()
        self.assertEqual(cfg.endpoint, "https://api.example.com")
        self.assertEqual(cfg.api_key, "sk-test")
        self.assertEqual(cfg.namespace, "prod")
        self.assertEqual(cfg.assistant_mode, "runagents")

    def test_trailing_slash_stripped(self):
        env = {"RUNAGENTS_ENDPOINT": "https://api.example.com/"}
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch("runagents.config._CONFIG_FILE", Path("/nonexistent/config.json")):
            cfg = load_config()
        self.assertEqual(cfg.endpoint, "https://api.example.com")

    def test_config_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"endpoint": "https://file.example.com", "api_key": "from-file"}, f)
            f.flush()
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch("runagents.config._CONFIG_FILE", Path(f.name)):
                cfg = load_config()
        os.unlink(f.name)
        self.assertEqual(cfg.endpoint, "https://file.example.com")
        self.assertEqual(cfg.api_key, "from-file")

    def test_env_overrides_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"endpoint": "https://file.example.com"}, f)
            f.flush()
            env = {"RUNAGENTS_ENDPOINT": "https://env.example.com"}
            with mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch("runagents.config._CONFIG_FILE", Path(f.name)):
                cfg = load_config()
        os.unlink(f.name)
        self.assertEqual(cfg.endpoint, "https://env.example.com")


class TestSaveConfig(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".runagents"
            config_file = config_dir / "config.json"
            with mock.patch("runagents.config._CONFIG_DIR", config_dir), \
                 mock.patch("runagents.config._CONFIG_FILE", config_file):
                cfg = Config(endpoint="https://saved.example.com", api_key="sk-saved")
                save_config(cfg)

                self.assertTrue(config_file.exists())
                data = json.loads(config_file.read_text())
                self.assertEqual(data["endpoint"], "https://saved.example.com")
                self.assertEqual(data["api_key"], "sk-saved")
                # 0600 permissions
                self.assertEqual(config_file.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
