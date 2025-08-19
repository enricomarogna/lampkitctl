from lampkitctl import db_ops


def test_create_database_and_user(monkeypatch) -> None:
    """Ensure database and user creation calls the correct SQL.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    recorded = {}

    def fake_run(cmd, dry_run, log_cmd=None, env=None):
        recorded["cmd"] = cmd
        recorded["log_cmd"] = list(log_cmd or [])
        recorded["env"] = env or {}

    monkeypatch.setattr(db_ops, "run_command", fake_run)
    db_ops.create_database_and_user(
        "mydb", "myuser", "mypw", root_password="secret", dry_run=True
    )
    assert "-psecret" not in recorded["cmd"]
    assert recorded["env"]["MYSQL_PWD"] == "secret"
    assert "-p******" not in recorded["log_cmd"]


def test_drop_database_and_user(monkeypatch) -> None:
    """Verify database and user removal executes SQL commands.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    called = {}

    def fake_run(cmd, dry_run, log_cmd=None, env=None):
        called["cmd"] = cmd
        called["env"] = env or {}

    monkeypatch.setattr(db_ops, "run_command", fake_run)
    db_ops.drop_database_and_user("mydb", "myuser", root_password="pw", dry_run=True)
    assert "mysql" in called["cmd"][0]
    assert called["env"]["MYSQL_PWD"] == "pw"
