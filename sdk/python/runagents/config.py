"""Configuration — matches cli/internal/config/config.go exactly.

Priority: env vars > ~/.runagents/config.json > defaults.
"""

import json
import os
import stat
from dataclasses import dataclass, asdict
from pathlib import Path

_CONFIG_DIR = Path.home() / ".runagents"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS = {
    "endpoint": "http://localhost:8092",
    "api_key": "",
    "namespace": "default",
    "assistant_mode": "external",
}


@dataclass
class Config:
    endpoint: str = _DEFAULTS["endpoint"]
    api_key: str = _DEFAULTS["api_key"]
    namespace: str = _DEFAULTS["namespace"]
    assistant_mode: str = _DEFAULTS["assistant_mode"]


def load_config() -> Config:
    """Load config: file → env overrides → defaults."""
    cfg = Config()

    # 1. Config file
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text())
            if data.get("endpoint"):
                cfg.endpoint = data["endpoint"]
            if data.get("api_key"):
                cfg.api_key = data["api_key"]
            if data.get("namespace"):
                cfg.namespace = data["namespace"]
            if data.get("assistant_mode"):
                cfg.assistant_mode = data["assistant_mode"]
        except (json.JSONDecodeError, OSError):
            pass

    # 2. Env var overrides
    if os.environ.get("RUNAGENTS_ENDPOINT"):
        cfg.endpoint = os.environ["RUNAGENTS_ENDPOINT"]
    if os.environ.get("RUNAGENTS_API_KEY"):
        cfg.api_key = os.environ["RUNAGENTS_API_KEY"]
    if os.environ.get("RUNAGENTS_NAMESPACE"):
        cfg.namespace = os.environ["RUNAGENTS_NAMESPACE"]
    if os.environ.get("RUNAGENTS_ASSISTANT_MODE"):
        cfg.assistant_mode = os.environ["RUNAGENTS_ASSISTANT_MODE"]

    # Strip trailing slash
    cfg.endpoint = cfg.endpoint.rstrip("/")
    return cfg


def save_config(cfg: Config) -> None:
    """Save config to ~/.runagents/config.json with 0600 permissions."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {k: v for k, v in asdict(cfg).items() if v}
    _CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
    _CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
