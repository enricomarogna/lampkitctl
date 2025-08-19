import subprocess
from lampkitctl import db_introspect


def test_sudo_defaults_file_fallback(monkeypatch):
    calls = []

    def fake_run(cmd, input=None, text=None, check=None, capture_output=None):
        calls.append(cmd)
        if "--protocol=socket" in cmd:
            raise subprocess.CalledProcessError(1, cmd, "fail")
        assert "--defaults-file=/etc/mysql/debian.cnf" in cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="alpha\nbeta\n", stderr="")

    monkeypatch.setattr(db_introspect.subprocess, "run", fake_run)

    dblist = db_introspect.list_databases_with_sudo("pw")
    assert dblist == ["alpha", "beta"]
    assert len(calls) == 2

