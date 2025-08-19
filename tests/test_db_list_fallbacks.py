import subprocess
from lampkitctl import db_introspect


def test_defaults_file_fallback(monkeypatch):
    calls = []

    def fake_check_output(cmd, env=None, text=None, stderr=None):
        calls.append(cmd)
        if len(calls) < 4:
            raise subprocess.CalledProcessError(1, cmd, output="fail")
        return "alpha\nbeta\n"

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)

    dblist = db_introspect.list_databases()
    assert dblist.databases == ["alpha", "beta"]
    assert calls[0][0] == "mysql"
    assert calls[1][0] == "mysql"
    assert calls[2][0] == "sudo"
    assert "--defaults-file=/etc/mysql/debian.cnf" in calls[3]


def test_tcp_success_after_password(monkeypatch):
    calls = []

    def fake_check_output(cmd, env=None, text=None, stderr=None):
        calls.append(cmd)
        if "--protocol=socket" in cmd:
            raise subprocess.CalledProcessError(1, cmd, output="socket fail")
        assert env.get("MYSQL_PWD") == "pw"
        assert "-h" in cmd and "127.0.0.1" in cmd
        return "mydb\n"

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)

    dblist = db_introspect.list_databases(password="pw")
    assert dblist.databases == ["mydb"]
    assert len(calls) == 2
