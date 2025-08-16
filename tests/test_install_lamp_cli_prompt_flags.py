import click
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


def test_flag_skips_confirm(monkeypatch):
    calls = []
    _setup_common(monkeypatch, calls)
    monkeypatch.setattr(
        click.testing._NamedTextIOWrapper,
        "isatty",
        lambda self: True,
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--dry-run", "install-lamp", "--set-db-root-pass"],
        input="strongpassword\nstrongpassword\n",
    )
    assert result.exit_code == 0
    assert "Set database root password now?" not in result.output
    assert calls[0][1] == "strongpassword"


def test_prompt_when_interactive(monkeypatch):
    calls = []
    _setup_common(monkeypatch, calls)
    monkeypatch.setattr(
        click.testing._NamedTextIOWrapper,
        "isatty",
        lambda self: True,
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--dry-run", "install-lamp"],
        input="y\nstrongpassword\nstrongpassword\n",
    )
    assert result.exit_code == 0
    assert "Set database root password now?" in result.output
    assert calls[0][1] == "strongpassword"


def test_env_provided(monkeypatch):
    calls = []
    _setup_common(monkeypatch, calls)
    runner = CliRunner()
    env = {"MY_PW": "supersecretpw"}
    result = runner.invoke(
        cli.cli,
        [
            "--dry-run",
            "install-lamp",
            "--set-db-root-pass",
            "--db-root-pass-env",
            "MY_PW",
        ],
        env=env,
    )
    assert result.exit_code == 0
    assert "Set database root password now?" not in result.output
    assert "Database root password" not in result.output
    assert calls[0][1] == "supersecretpw"
