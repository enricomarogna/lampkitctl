from lampkitctl import db_ops


def test_create_database_and_user(monkeypatch):
    recorded = {}

    def fake_run(cmd, dry_run, log_cmd=None):
        recorded["cmd"] = cmd
        recorded["log_cmd"] = list(log_cmd or [])

    monkeypatch.setattr(db_ops, "run_command", fake_run)
    db_ops.create_database_and_user(
        "mydb", "myuser", "mypw", root_password="secret", dry_run=True
    )
    assert any(part.startswith("-psecret") for part in recorded["cmd"])
    assert "-p******" in recorded["log_cmd"]


def test_drop_database_and_user(monkeypatch):
    called = {}

    def fake_run(cmd, dry_run, log_cmd=None):
        called["cmd"] = cmd

    monkeypatch.setattr(db_ops, "run_command", fake_run)
    db_ops.drop_database_and_user("mydb", "myuser", dry_run=True)
    assert "mysql" in called["cmd"][0]
