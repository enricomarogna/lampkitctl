from click.testing import CliRunner
from lampkitctl import cli


def test_cli_install_lamp(monkeypatch) -> None:
    """Validate installation command sequence for LAMP services.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    calls = []
    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "check_service", lambda s: False)
    monkeypatch.setattr(
        cli.system_ops, "install_service", lambda s, dry_run: calls.append(s)
    )
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--dry-run", "install-lamp"])
    assert result.exit_code == 0
    assert calls == ["apache2", "mysql", "php"]


def test_cli_create_site(monkeypatch) -> None:
    """Ensure the CLI orchestrates site creation steps.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(
        cli.system_ops, "create_web_directory", lambda *a, **k: None
    )
    monkeypatch.setattr(
        cli.system_ops, "create_virtualhost", lambda *a, **k: None
    )
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


def test_cli_uninstall_site(monkeypatch) -> None:
    """Validate removal of a site through the CLI.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(cli.utils, "prompt_confirm", lambda *a, **k: True)
    monkeypatch.setattr(
        cli.system_ops, "remove_virtualhost", lambda *a, **k: None
    )
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


def test_cli_list_sites(monkeypatch) -> None:
    """Check that configured sites are listed correctly.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    monkeypatch.setattr(
        cli.preflight,
        "has_cmd",
        lambda name, msg=None, severity=cli.preflight.Severity.BLOCKING: cli.preflight.CheckResult(True, ""),
    )
    monkeypatch.setattr(
        cli.preflight, "apache_paths_present", lambda: cli.preflight.CheckResult(True, "")
    )
    monkeypatch.setattr(
        cli.system_ops, "list_sites", lambda: [{"domain": "a", "doc_root": "/var/www/a"}]
    )
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["list-sites"])
    assert "a -> /var/www/a" in result.output
