from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

_WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_TEMP_SLUG = f"pytest-{_WORKSPACE_ROOT.name}"
_EXTERNAL_TEMP_ROOT = Path.home() / ".tmp" / _PROJECT_TEMP_SLUG
_EXTERNAL_PYTEST_TEMP_ROOT = _EXTERNAL_TEMP_ROOT / "tmp"
_EXTERNAL_PYTEST_CACHE_DIR = _EXTERNAL_TEMP_ROOT / "cache"


def _patch_pytest_tempdir_acl_behavior() -> None:
    """Use inherited ACLs for pytest temp dirs on Windows.

    In this Codex/Windows sandbox, pytest's default ``mode=0o700`` directory
    creation can yield temp roots that the active shell identity can stat but
    not enumerate or clean up. Creating the same directories without an
    explicit mode inherits the parent ACLs and keeps tmp_path teardown working.
    """

    if os.name != "nt":
        return

    import _pytest.pathlib as pytest_pathlib
    import _pytest.tmpdir as pytest_tmpdir

    def _safe_mkdtemp(
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | os.PathLike[str] | None = None,
    ) -> str:
        suffix = suffix or ""
        prefix = prefix or "tmp"
        parent = Path(dir) if dir is not None else _EXTERNAL_PYTEST_TEMP_ROOT
        parent.mkdir(parents=True, exist_ok=True)

        for _ in range(10):
            new_path = parent / f"{prefix}{uuid.uuid4().hex[:8]}{suffix}"
            try:
                new_path.mkdir()
            except FileExistsError:
                continue
            return str(new_path)
        raise OSError("could not create temp dir with inherited ACLs")

    def _safe_make_numbered_dir(root: Path, prefix: str, mode: int = 0o700) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        new_path = Path(_safe_mkdtemp(prefix=prefix, dir=root))
        pytest_pathlib._force_symlink(root, prefix + "current", new_path)
        return new_path

    def _safe_getbasetemp(self: pytest_tmpdir.TempPathFactory) -> Path:
        if self._basetemp is not None:
            return self._basetemp

        if self._given_basetemp is not None:
            basetemp = self._given_basetemp
            if basetemp.exists():
                pytest_pathlib.rm_rf(basetemp)
            basetemp.parent.mkdir(parents=True, exist_ok=True)
            basetemp.mkdir()
            basetemp = basetemp.resolve()
            self._basetemp = basetemp
            self._trace("new basetemp", basetemp)
            return basetemp

        workspace_basetemp = _EXTERNAL_PYTEST_TEMP_ROOT / "basetemp"
        if workspace_basetemp.exists():
            pytest_pathlib.rm_rf(workspace_basetemp)
        workspace_basetemp.parent.mkdir(parents=True, exist_ok=True)
        workspace_basetemp.mkdir()
        workspace_basetemp = workspace_basetemp.resolve()
        self._basetemp = workspace_basetemp
        self._trace("new basetemp", workspace_basetemp)
        return workspace_basetemp

    tempfile.mkdtemp = _safe_mkdtemp
    pytest_pathlib.make_numbered_dir = _safe_make_numbered_dir
    pytest_tmpdir.make_numbered_dir = _safe_make_numbered_dir
    pytest_tmpdir.TempPathFactory.getbasetemp = _safe_getbasetemp


_patch_pytest_tempdir_acl_behavior()


def pytest_configure(config: pytest.Config) -> None:
    if os.name != "nt":
        return

    if not config.option.basetemp:
        config.option.basetemp = str(_EXTERNAL_PYTEST_TEMP_ROOT / "basetemp")

    config._inicache["cache_dir"] = str(_EXTERNAL_PYTEST_CACHE_DIR)


@pytest.fixture
def workspace_tmp_path() -> Path:
    root = _EXTERNAL_PYTEST_TEMP_ROOT / "workspace"
    root.mkdir(parents=True, exist_ok=True)
    temp_path = root / f"p-{uuid.uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=False)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)
