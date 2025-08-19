from lampkitctl import db_ops


def test_drop_database_and_user_host_parse(monkeypatch) -> None:
    sqls: list[str] = []

    def fake_run(cmd, dry_run, log_cmd=None):
        sqls.append(cmd[-1])

    monkeypatch.setattr(db_ops, "run_command", fake_run)

    db_ops.drop_database_and_user("mydb", "alice@host", dry_run=True)
    assert "DROP USER IF EXISTS 'alice'@'host';" in sqls[-1]

    db_ops.drop_database_and_user("mydb", "bob", dry_run=True)
    assert "DROP USER IF EXISTS 'bob'@'localhost';" in sqls[-1]

