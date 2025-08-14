import subprocess

from lampkitctl import preflight
from lampkitctl import preflight_locks


def test_detect_lock_lslocks(monkeypatch):
    sample = "915 unattended-upgr /var/lib/dpkg/lock-frontend\n"

    monkeypatch.setattr(preflight_locks, "_run", lambda c: (0, sample))
    info = preflight_locks.detect_lock()
    assert info.locked
    assert info.holder_pid == 915
    assert info.holder_cmd == "unattended-upgr"
    assert info.path == "/var/lib/dpkg/lock-frontend"


def test_unattended_without_lock_warn(monkeypatch):
    monkeypatch.setattr(preflight_locks, "detect_lock", lambda: preflight_locks.LockInfo(False))

    class P:
        stdout = "unattended-upgrades\n"
        stderr = ""
        returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: P())
    res = preflight.apt_lock(preflight.Severity.BLOCKING)
    assert not res.ok
    assert res.severity is preflight.Severity.WARNING
