from lampkitctl import db_introspect


def test_user_list_filters_and_sorts(monkeypatch) -> None:
    def fake_check_output(cmd, env=None, text=None, stderr=None):
        return (
            "bob@localhost\n"
            "mysql.sys@localhost\n"
            "debian-sys-maint@localhost\n"
            "alice@localhost\n"
            "root@localhost\n"
        )

    monkeypatch.setattr(db_introspect.subprocess, "check_output", fake_check_output)
    users = db_introspect.list_users().items
    assert users == ["alice@localhost", "bob@localhost"]

