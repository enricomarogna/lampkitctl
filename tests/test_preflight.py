import os
import os
import subprocess
from pathlib import Path

import pytest

from lampkitctl import preflight


def test_is_root_or_sudo(monkeypatch):
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    assert preflight.is_root_or_sudo().ok
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.delenv("SUDO_UID", raising=False)
    assert not preflight.is_root_or_sudo().ok


def test_is_supported_os(monkeypatch):
    data = "ID=ubuntu\nVERSION_ID=\"22.04\"\n"
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: data)
    assert preflight.is_supported_os().ok
    data = "ID=ubuntu\nVERSION_ID=\"18.04\"\n"
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: data)
    assert not preflight.is_supported_os().ok


def test_has_cmd(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda n: "/bin/true")
    assert preflight.has_cmd("true").ok
    monkeypatch.setattr(preflight.shutil, "which", lambda n: None)
    assert not preflight.has_cmd("true").ok


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
    assert preflight.apache_paths_present().ok
    monkeypatch.setattr(Path, "exists", lambda self: False)
    assert not preflight.apache_paths_present().ok


def test_can_write(monkeypatch):
    monkeypatch.setattr(os, "access", lambda p, m: True)
    assert preflight.can_write("/tmp").ok
    monkeypatch.setattr(os, "access", lambda p, m: False)
    assert not preflight.can_write("/tmp").ok


def test_apt_lock_suspected(monkeypatch):
    class P:
        stdout = "apt"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: P())
    res = preflight.apt_lock_suspected()
    assert not res.ok and res.severity is preflight.Severity.WARNING


def test_is_wordpress_dir(tmp_path):
    (tmp_path / "wp-config.php").write_text("")
    (tmp_path / "wp-content").mkdir()
    (tmp_path / "wp-includes").mkdir()
    assert preflight.is_wordpress_dir(tmp_path).ok
    assert not preflight.is_wordpress_dir(tmp_path / "empty").ok


def test_ensure_or_fail(monkeypatch):
    checks = [preflight.CheckResult(False, "missing")]
    with pytest.raises(SystemExit):
        preflight.ensure_or_fail(checks, interactive=False)
    # interactive warning path
    monkeypatch.setattr(
        preflight.utils, "prompt_confirm", lambda *a, **k: True
    )
    checks = [
        preflight.CheckResult(False, "warn", preflight.Severity.WARNING)
    ]
    preflight.ensure_or_fail(checks, interactive=True)
