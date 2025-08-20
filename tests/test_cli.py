from click.testing import CliRunner
from lampkitctl import cli, packages, preflight, preflight_locks, utils


def test_cli_install_lamp(monkeypatch) -> None:
    """Ensure CLI passes DB engine to installer."""

    calls = []
    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(cli.preflight, "apt_lock", lambda *a, **k: preflight.CheckResult(True, ""))
    monkeypatch.setattr(cli.preflight_locks, "wait_for_lock", lambda *a, **k: preflight_locks.LockInfo(False))

    def fake_install(pref, dry_run=False):
        calls.append(pref)
        return packages.Engine("mariadb", "mariadb-server", "mariadb-client", "mariadb")

    monkeypatch.setattr(cli.system_ops, "install_lamp_stack_full", fake_install)
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--dry-run", "install-lamp", "--db-engine", "mariadb"], input="n\n"
    )
    assert result.exit_code == 0
    assert calls == ["mariadb"]


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
    monkeypatch.setattr(cli.preflight, "apt_lock", lambda *a, **k: preflight.CheckResult(True, ""))
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


def test_cli_uninstall_site_env_pass(monkeypatch) -> None:
    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(cli.utils, "prompt_confirm", lambda *a, **k: True)
    monkeypatch.setattr(cli.system_ops, "remove_virtualhost", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "remove_host_entry", lambda *a, **k: None)
    monkeypatch.setattr(cli.system_ops, "remove_web_directory", lambda *a, **k: None)
    seen = {}

    def fake_drop(db_name, db_user, *, root_password, dry_run):
        seen["root_password"] = root_password

    monkeypatch.setattr(cli.db_ops, "drop_database_and_user", fake_drop)
    runner = CliRunner()
    env = {"LAMPKITCTL_DB_ROOT_PASS": "pw"}
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
        env=env,
    )
    assert result.exit_code == 0
    assert seen["root_password"] == "pw"


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
        cli.system_ops,
        "list_sites",
        lambda: [{"domain": "a.com", "doc_root": "/var/www/a"}],
    )
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["list-sites"])
    domain_w = max(len("DOMAIN"), len("a.com"))
    path_w = max(len("PATH"), len("/var/www/a"))
    expected_header = f"{'DOMAIN'.ljust(domain_w)} | {'PATH'.ljust(path_w)}"
    expected_sep = f"{'-' * domain_w}-+-{'-' * path_w}"
    expected_row = f"{'a.com'.ljust(domain_w)} | /var/www/a"
    lines = result.output.splitlines()
    assert lines[0] == expected_header
    assert lines[1] == expected_sep
    assert lines[2] == expected_row
    assert "->" not in result.output
    assert len(lines) == 3


def test_cli_list_sites_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        cli.preflight,
        "has_cmd",
        lambda name, msg=None, severity=cli.preflight.Severity.BLOCKING: cli.preflight.CheckResult(True, ""),
    )
    monkeypatch.setattr(
        cli.preflight, "apache_paths_present", lambda: cli.preflight.CheckResult(True, "")
    )
    monkeypatch.setattr(cli.system_ops, "list_sites", lambda: [])
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["list-sites"])
    assert "No sites found" in result.output
