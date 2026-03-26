from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def workspace_tmp_path() -> Path:
    root = Path(__file__).resolve().parents[1] / ".t"
    root.mkdir(parents=True, exist_ok=True)
    temp_path = root / f"p-{uuid.uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=False)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)
