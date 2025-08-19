import subprocess
from lampkitctl import db_introspect


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
    assert dblist == ["mydb"]
    assert len(calls) == 2
