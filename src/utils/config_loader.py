import os
from pathlib import Path
from typing import Any

import yaml


class ConfigLoader:
    """Load project configuration.

    By default the loader reads YAML files from ``config/``.  The V0.2 CLI can
    point the whole pipeline to a per-project runtime config directory by
    setting ``PAPER_AGENT_CONFIG_DIR``.  Existing modules can keep using
    ``ConfigLoader()`` without knowing where the runtime config lives.
    """

    ENV_NAME = "PAPER_AGENT_CONFIG_DIR"

    def __init__(self, config_dir: str | None = None):
        resolved_dir = config_dir or os.getenv(self.ENV_NAME) or "config"
        self.config_dir = Path(resolved_dir)

    def _load_yaml(self, filename: str) -> dict:
        file_path = self.config_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return self._normalize_legacy_values(data)

    def _normalize_legacy_values(self, value: Any) -> Any:
        """Normalize common legacy typos in YAML values.

        Older runtime.yaml files used ``ture`` instead of ``true``.  YAML treats
        it as a string, which can lead to confusing behavior.  Normalizing here
        keeps old configs usable and makes the rest of the code receive real
        booleans.
        """
        if isinstance(value, dict):
            return {k: self._normalize_legacy_values(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._normalize_legacy_values(v) for v in value]
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered == "ture":
                return True
            if lowered == "true":
                return True
            if lowered == "false":
                return False
        return value

    def load_models_config(self) -> dict:
        return self._load_yaml("models.yaml")

    def load_runtime_config(self) -> dict:
        return self._load_yaml("runtime.yaml")

    def load_paths_config(self) -> dict:
        return self._load_yaml("paths.yaml")

    def load_all(self) -> dict:
        return {
            "models": self.load_models_config(),
            "runtime": self.load_runtime_config(),
            "paths": self.load_paths_config()
        }
