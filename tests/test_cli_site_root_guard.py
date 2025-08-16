from click.testing import CliRunner

from lampkitctl import cli


def test_create_site_guard_invokes_sudo(monkeypatch):
    called = {}

    def fake_reexec(argv, non_interactive, dry_run):
        called["argv"] = argv
        raise SystemExit(1)

    monkeypatch.setattr(cli, "maybe_reexec_with_sudo", fake_reexec)

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
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

    assert result.exit_code == 1
    assert called["argv"]
