import subprocess

import subprocess

from lampkitctl import db_detect


class Proc:
    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def _fake_run_factory(output: str):
    def fake_run(cmd, capture_output=True, text=True):
        if cmd[:2] == ["apt-cache", "policy"]:
            return Proc("Installed: (none)\n")
        if cmd[:2] == ["mysql", "--version"]:
            return Proc(output)
        raise AssertionError(f"unexpected command: {cmd}")

    return fake_run


def test_detect_from_version_mariadb(monkeypatch):
    fake_run = _fake_run_factory("mysql  Ver 15.1 Distrib 10.5.5-MariaDB, for Linux")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert db_detect.detect_db_engine() == "mariadb"


def test_detect_from_version_mysql(monkeypatch):
    fake_run = _fake_run_factory("mysql  Ver 8.0.33 for Linux on x86_64 (MySQL Community Server - GPL)")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert db_detect.detect_db_engine() == "mysql"
