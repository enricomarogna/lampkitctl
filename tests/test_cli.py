from click.testing import CliRunner
from lampkitctl import cli


def test_cli_install_lamp(monkeypatch):
    calls = []
    monkeypatch.setattr(cli.system_ops, "check_service", lambda s: False)
    monkeypatch.setattr(cli.system_ops, "install_service", lambda s, dry_run: calls.append(s))
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--dry-run", "install-lamp"])
    assert result.exit_code == 0
    assert calls == ["apache2", "mysql", "php"]


def test_cli_create_site(monkeypatch):
    monkeypatch.setattr(cli.system_ops, "create_web_directory", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "create_virtualhost", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "enable_site", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "add_host_entry", lambda *a, **k: None)
    monkeypatch.setattr(cli.db_ops, "create_database_and_user", lambda *a, **k: None)
    monkeypatch.setattr(cli.wp_ops, "install_wordpress", lambda *a, **k: None)
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "create-site",
            "example.com",
            "--doc-root=/var/www/example",
            "--db-name=db",
            "--db-user=user",
            "--db-password",
            "pass",
        ],
    )
    assert result.exit_code == 0


def test_cli_uninstall_site(monkeypatch):
    monkeypatch.setattr(cli.utils, "prompt_confirm", lambda *a, **k: True)
    monkeypatch.setattr(cli.system_ops, "remove_virtualhost", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "remove_host_entry", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "remove_web_directory", lambda *a, **k: None)
    monkeypatch.setattr(cli.db_ops, "drop_database_and_user", lambda *a, **k: None)
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "uninstall-site",
            "example.com",
            "--doc-root=/var/www/example",
            "--db-name=db",
            "--db-user=user",
        ],
    )
    assert result.exit_code == 0


def test_cli_list_sites(monkeypatch):
    monkeypatch.setattr(cli.system_ops, "list_sites", lambda: [{"domain": "a", "doc_root": "/var/www/a"}])
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["list-sites"])
    assert "a -> /var/www/a" in result.output
