from click.testing import CliRunner

from lampkitctl import cli, packages, system_ops


def test_install_lamp_cli(monkeypatch):
    calls = []
    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    fake_engine = packages.Engine("mysql", "mysql-server", "mysql-client", "mysql")
    monkeypatch.setattr(system_ops, "detect_db_engine", lambda preferred: fake_engine)

    monkeypatch.setattr(system_ops, "refresh_cache", lambda **k: calls.append("update"))

    def fake_run(cmd, dry_run=False, capture_output=False, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(system_ops, "run_command", fake_run)
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--dry-run", "install-lamp"])
    assert result.exit_code == 0
    install_cmd = calls[1]
    assert "mysql-server" in install_cmd
    for pkg in packages.PHP_BASE + packages.PHP_EXTRAS:
        assert pkg in install_cmd
