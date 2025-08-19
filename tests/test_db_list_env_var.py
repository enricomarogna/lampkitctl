from types import SimpleNamespace
from lampkitctl import menu, db_introspect

def test_db_list_env_var(monkeypatch):
    db_introspect._CACHED_ROOT_PASSWORD = None
    monkeypatch.setenv("LAMPKITCTL_DB_ROOT_PASS", "pw")
    env_calls = []

    def fake_check_output(cmd, env=None, text=None, stderr=None):
        env_calls.append(env.get("MYSQL_PWD"))
        return "mydb\n"

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)

    def fake_secret(message):
        raise AssertionError("prompt should not be called")

    menu.inquirer = SimpleNamespace(secret=fake_secret)

    dblist = menu._list_dbs_interactive()
    assert dblist == ["mydb"]
    assert env_calls == ["pw"]
