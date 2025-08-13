import os
from pathlib import Path

import pytest

from lampkitctl import launcher


def _fake_console(tmp_path: Path) -> Path:
    console = tmp_path / "venv/bin/lampkitctl"
    console.parent.mkdir(parents=True)
    console.write_text("#!/bin/bash\n")
    os.chmod(console, 0o755)
    return console


def test_install_launcher_writes_executable(tmp_path, monkeypatch):
    exe = _fake_console(tmp_path)
    monkeypatch.setattr(launcher, "resolve_self_executable", lambda: str(exe))
    dest = tmp_path / "bin"
    path = launcher.install_launcher(preferred_dir=str(dest))
    assert path.read_text().startswith("#!/usr/bin/env bash")
    assert str(exe) in path.read_text()
    assert os.access(path, os.X_OK)


def test_install_launcher_force_overwrite(tmp_path, monkeypatch):
    exe = _fake_console(tmp_path)
    monkeypatch.setattr(launcher, "resolve_self_executable", lambda: str(exe))
    dest = tmp_path / "bin"
    launcher.install_launcher(preferred_dir=str(dest))
    with pytest.raises(SystemExit):
        launcher.install_launcher(preferred_dir=str(dest))
    launcher.install_launcher(preferred_dir=str(dest), force=True)
    assert os.access(dest / "lampkitctl", os.X_OK)


def test_uninstall_launcher(tmp_path, monkeypatch):
    exe = _fake_console(tmp_path)
    monkeypatch.setattr(launcher, "resolve_self_executable", lambda: str(exe))
    dest = tmp_path / "bin"
    path = launcher.install_launcher(preferred_dir=str(dest))
    removed = launcher.uninstall_launcher(preferred_dir=str(dest))
    assert removed == path
    assert not path.exists()
