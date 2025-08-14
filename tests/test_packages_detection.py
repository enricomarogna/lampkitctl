import subprocess

from lampkitctl import packages


class Proc:
    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def test_detect_mysql_from_policy(monkeypatch):
    sample = {
        "mysql-server": "mysql-server:\n  Candidate: 8.0.43-0ubuntu0.24.04.1\n",
        "mariadb-server": "mariadb-server:\n  Candidate: 1:10.11.13-0ubuntu0.24.04.1\n",
        "default-mysql-server": "default-mysql-server:\n  Candidate: 1.1.0build1\n",
    }

    def fake_run(cmd, capture_output=True, text=True):
        pkg = cmd[-1]
        return Proc(sample.get(pkg, ""))

    monkeypatch.setattr(subprocess, "run", fake_run)
    eng = packages.detect_db_engine(None)
    assert eng.name == "mysql"

