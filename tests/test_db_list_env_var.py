from lampkitctl import db_introspect, auth_cache


def test_db_list_env_var(monkeypatch):
    auth_cache.clear()
    monkeypatch.setenv("LAMPKITCTL_DB_ROOT_PASS", "pw")
    env_calls = []

    def fake_check_output(cmd, env=None, text=None, stderr=None):
        env_calls.append(env.get("MYSQL_PWD"))
        return "mydb\n"

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)

    dblist = db_introspect.list_databases()
    assert dblist == ["mydb"]
    assert env_calls == ["pw"]
