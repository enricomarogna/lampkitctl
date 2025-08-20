import subprocess

from lampkitctl import db_detect


class Proc:
    def __init__(self, stdout: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def test_detect_mysql_via_dpkg(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        if cmd[:2] == ["apt-cache", "policy"]:
            pkg = cmd[2]
            if pkg == "mysql-server":
                return Proc("Installed: 8.0\n")
            if pkg == "mariadb-server":
                return Proc("Installed: (none)\n")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert db_detect.detect_db_engine() == "mysql"


def test_detect_mariadb_via_dpkg(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        if cmd[:2] == ["apt-cache", "policy"]:
            pkg = cmd[2]
            if pkg == "mysql-server":
                return Proc("Installed: (none)\n")
            if pkg == "mariadb-server":
                return Proc("Installed: 10.5\n")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert db_detect.detect_db_engine() == "mariadb"


def test_detect_none_via_dpkg(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        if cmd[:2] == ["apt-cache", "policy"]:
            return Proc("Installed: (none)\n")
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert db_detect.detect_db_engine() is None
