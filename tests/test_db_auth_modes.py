from click.testing import CliRunner

from lampkitctl import cli, db_ops, system_ops, preflight


def test_db_auth_modes(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(cli.preflight, "apt_lock", lambda *a, **k: preflight.CheckResult(True, ""))
    monkeypatch.setattr(system_ops, "create_web_directory", lambda *a, **k: None)
    monkeypatch.setattr(system_ops, "create_virtualhost", lambda *a, **k: None)
    monkeypatch.setattr(system_ops, "enable_site", lambda *a, **k: None)
    monkeypatch.setattr(system_ops, "add_host_entry", lambda *a, **k: None)

    captured = {}

    def fake_create(db_name, user, pwd, root_password=None, dry_run=False):
        captured["root"] = root_password

    monkeypatch.setattr(db_ops, "create_database_and_user", fake_create)

    monkeypatch.setattr(db_ops, "detect_engine", lambda: "mariadb")
    runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "create-site",
            "example.com",
            "--doc-root",
            "/var/www/example",
            "--db-name",
            "db",
            "--db-user",
            "user",
            "--db-password",
            "pw",
        ],
    )
    assert captured["root"] is None

    monkeypatch.setattr(db_ops, "detect_engine", lambda: "mysql")
    runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "create-site",
            "example.com",
            "--doc-root",
            "/var/www/example",
            "--db-name",
            "db",
            "--db-user",
            "user",
            "--db-password",
            "pw",
            "--db-root-auth",
            "password",
            "--db-root-pass",
            "rootpw",
        ],
    )
    assert captured["root"] == "rootpw"

    runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "create-site",
            "example.com",
            "--doc-root",
            "/var/www/example",
            "--db-name",
            "db",
            "--db-user",
            "user",
            "--db-password",
            "pw",
            "--db-root-auth",
            "socket",
        ],
    )
    assert captured["root"] is None
