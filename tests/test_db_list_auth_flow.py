from types import SimpleNamespace
import subprocess
from lampkitctl import menu, db_introspect


def test_db_list_auth_flow(monkeypatch):
    db_introspect._CACHED_ROOT_PASSWORD = None
    env_calls = []

    def fake_check_output(cmd, env=None, text=None, stderr=None):
        env_calls.append(env.get("MYSQL_PWD") if env else None)
        if env and env.get("MYSQL_PWD") == "pw":
            return "alpha\nbeta\n"
        raise subprocess.CalledProcessError(1, cmd, output="ERROR")

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)

    secrets = []

    def fake_secret(message):
        secrets.append(message)

        class R:
            def execute(self):
                return "pw"

        return R()

    menu.inquirer = SimpleNamespace(secret=fake_secret)

    dblist = menu._list_dbs_interactive()
    assert dblist == ["alpha", "beta"]
    assert secrets == ["Database root password:"]
    assert env_calls == [None, None, None, None, "pw"]
