import os
from pathlib import Path

from src.env_bootstrap import load_local_env


def test_load_local_env_populates_appeears_token_from_env_local(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env.local"
    env_path.write_text("APPEEARS_API_TOKEN=test-token\n", encoding="utf-8")
    monkeypatch.delenv("APPEEARS_API_TOKEN", raising=False)

    loaded_path = load_local_env(project_root=tmp_path)

    assert loaded_path == env_path
    assert os.getenv("APPEEARS_API_TOKEN") == "test-token"


def test_load_local_env_does_not_override_existing_environment(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env.local"
    env_path.write_text("APPEEARS_API_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setenv("APPEEARS_API_TOKEN", "existing-token")

    load_local_env(project_root=tmp_path)

    assert os.getenv("APPEEARS_API_TOKEN") == "existing-token"
