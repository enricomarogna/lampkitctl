import logging
from click.testing import CliRunner

from lampkitctl import cli, db_ops, packages, system_ops
from lampkitctl import preflight, preflight_locks, utils


def _setup_common(monkeypatch, calls):
    monkeypatch.setattr(cli.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(
        cli.preflight_locks, "wait_for_lock", lambda *a, **k: preflight_locks.LockInfo(False)
    )
    monkeypatch.setattr(
        cli.preflight_locks, "detect_lock", lambda: preflight_locks.LockInfo(False)
    )
    fake_engine = packages.Engine("mysql", "mysql-server", "mysql-client", "mysql")
    monkeypatch.setattr(system_ops, "install_lamp_stack", lambda *a, **k: fake_engine)
    monkeypatch.setattr(system_ops, "ensure_db_ready", lambda **k: True)
    monkeypatch.setattr(cli.utils, "setup_logging", lambda *a, **k: None)

    def fake_set(engine, password, plugin, dry_run=False):
        calls.append((engine, password, plugin, dry_run))

    monkeypatch.setattr(db_ops, "set_root_password", fake_set)


def test_interactive_flow(monkeypatch):
    calls = []
    _setup_common(monkeypatch, calls)
    runner = CliRunner()
    pw = "supersecretpw1"
    result = runner.invoke(
        cli.cli,
        ["--dry-run", "install-lamp"],
        input=f"y\n{pw}\n{pw}\n",
    )
    assert result.exit_code == 0
    assert calls[0][1] == pw


def test_non_interactive_env(monkeypatch):
    calls = []
    _setup_common(monkeypatch, calls)
    runner = CliRunner()
    env = {"MY_PW": "supersecretpw2"}
    result = runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "--non-interactive",
            "install-lamp",
            "--db-root-pass-env",
            "MY_PW",
            "--db-root-plugin",
            "mysql_native_password",
        ],
        env=env,
    )
    assert result.exit_code == 0
    assert calls[0][1] == "supersecretpw2"
    assert calls[0][2] == "mysql_native_password"


def test_non_interactive_no_pass(monkeypatch):
    calls = []
    _setup_common(monkeypatch, calls)
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--dry-run", "--non-interactive", "install-lamp"]
    )
    assert result.exit_code == 0
    assert not calls
    assert "Skipping database root password" in result.output


def test_masking(monkeypatch, caplog):
    calls = []
    _setup_common(monkeypatch, calls)
    caplog.set_level(logging.INFO)
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "install-lamp",
            "--set-db-root-pass",
            "--db-root-pass",
            "supersecretpw3",
        ],
    )
    assert result.exit_code == 0
    assert any(
        getattr(r, "db_root_pass", None) == utils.SECRET_PLACEHOLDER
        for r in caplog.records
    )
