from __future__ import annotations

import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - exercised when python-dotenv is unavailable locally
    def load_dotenv(dotenv_path: Path, override: bool = False) -> bool:
        loaded_any = False
        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not key:
                continue
            if override or key not in os.environ:
                os.environ[key] = value
            loaded_any = True
        return loaded_any

logger = logging.getLogger(__name__)


def load_local_env(project_root: Path | None = None) -> Path | None:
    """Load .env.local for local development without overriding real environment variables."""
    root = project_root or Path.cwd()
    env_path = root / ".env.local"
    if not env_path.exists():
        return None

    load_dotenv(dotenv_path=env_path, override=False)
    return env_path


def log_loaded_local_env(env_path: Path | None) -> None:
    if env_path is None:
        return
    logger.info("Loaded local environment from %s", env_path)
