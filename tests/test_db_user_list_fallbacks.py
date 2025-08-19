import subprocess
from lampkitctl import db_introspect


def test_user_sudo_defaults_file_fallback(monkeypatch) -> None:
    calls = []

    def fake_run(cmd, input=None, text=None, check=None, capture_output=None):
        calls.append(cmd)
        if "--protocol=socket" in cmd:
            raise subprocess.CalledProcessError(1, cmd, "fail")
        assert "--defaults-file=/etc/mysql/debian.cnf" in cmd
        return subprocess.CompletedProcess(
            cmd, 0, stdout="beta@localhost\nalpha@localhost\n", stderr=""
        )

    monkeypatch.setattr(db_introspect.subprocess, "run", fake_run)

    users = db_introspect.list_users_with_sudo("pw")
    assert users.items == ["alpha@localhost", "beta@localhost"]
    assert len(calls) == 2

