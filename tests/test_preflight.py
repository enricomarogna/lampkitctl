import os
import subprocess
from pathlib import Path

import pytest

from lampkitctl import preflight


def test_is_root_or_sudo(monkeypatch):
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    assert preflight.is_root_or_sudo()
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.delenv("SUDO_UID", raising=False)
    assert not preflight.is_root_or_sudo()


def test_is_supported_os(monkeypatch):
    data = "ID=ubuntu\nVERSION_ID=\"22.04\"\n"
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: data)
    assert preflight.is_supported_os()
    data = "ID=ubuntu\nVERSION_ID=\"18.04\"\n"
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: data)
    assert not preflight.is_supported_os()


def test_has_cmd(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda n: "/bin/true")
    assert preflight.has_cmd("true")
    monkeypatch.setattr(preflight.shutil, "which", lambda n: None)
    assert not preflight.has_cmd("true")


def test_service_running(monkeypatch):
    class R:
        returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
    assert preflight.service_running("apache2")

    class F:
        returncode = 3

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: F())
    assert not preflight.service_running("apache2")


def test_apache_paths_present(monkeypatch):
    def fake_exists(self):
        return str(self) in {"/etc/apache2", "/etc/apache2/sites-available"}

    monkeypatch.setattr(Path, "exists", fake_exists)
    assert preflight.apache_paths_present()
    monkeypatch.setattr(Path, "exists", lambda self: False)
    assert not preflight.apache_paths_present()


def test_can_write(monkeypatch):
    monkeypatch.setattr(os, "access", lambda p, m: True)
    assert preflight.can_write("/tmp")
    monkeypatch.setattr(os, "access", lambda p, m: False)
    assert not preflight.can_write("/tmp")


def test_is_wordpress_dir(tmp_path):
    (tmp_path / "wp-config.php").write_text("")
    (tmp_path / "wp-content").mkdir()
    (tmp_path / "wp-includes").mkdir()
    assert preflight.is_wordpress_dir(tmp_path)
    assert not preflight.is_wordpress_dir(tmp_path / "empty")


def test_collect_errors_and_ensure(monkeypatch):
    checks = [lambda: "missing", lambda: None]
    assert preflight.collect_errors(checks) == ["missing"]
    with pytest.raises(SystemExit):
        preflight.ensure_or_fail(checks, "cmd", interactive=False)
    # interactive continue
    monkeypatch.setattr(preflight.utils, "prompt_confirm", lambda *a, **k: True)
    preflight.ensure_or_fail(checks, "cmd", interactive=True)
