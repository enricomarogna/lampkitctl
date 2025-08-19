from lampkitctl import db_introspect, auth_cache


def test_cache_root_password(monkeypatch):
    auth_cache.clear()
    auth_cache.set_db_root_password("secret")
    seen = []

    def fake_check_output(cmd, env=None, text=None, stderr=None):
        seen.append(env.get("MYSQL_PWD"))
        return "db1\n"

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)

    dblist = db_introspect.list_databases()
    assert dblist == ["db1"]
    assert seen == ["secret"]
