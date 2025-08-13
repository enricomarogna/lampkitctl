import subprocess

from lampkitctl import packages


class Proc:
    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def test_detect_prefers_mysql(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        pkg = cmd[-1]
        if pkg == "mysql-server":
            return Proc("Candidate: 8.0\n")
        if pkg == "mariadb-server":
            return Proc("Candidate: 10.5\n")
        return Proc("", returncode=1)
    monkeypatch.setattr(subprocess, "run", fake_run)
    eng = packages.detect_db_engine(None)
    assert eng.server_pkg == "mysql-server"


def test_detect_only_mariadb(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        pkg = cmd[-1]
        if pkg == "mysql-server":
            return Proc("Candidate: (none)\n")
        if pkg == "mariadb-server":
            return Proc("Candidate: 10.5\n")
        return Proc("", returncode=1)
    monkeypatch.setattr(subprocess, "run", fake_run)
    eng = packages.detect_db_engine(None)
    assert eng.server_pkg == "mariadb-server"


def test_detect_fallback(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        pkg = cmd[-1]
        if pkg == "mysql-server":
            return Proc("Candidate: (none)\n")
        if pkg == "mariadb-server":
            return Proc("Candidate: 10.5\n")
        return Proc("", returncode=1)
    monkeypatch.setattr(subprocess, "run", fake_run)
    eng = packages.detect_db_engine("mysql")
    assert eng.server_pkg == "mariadb-server"
