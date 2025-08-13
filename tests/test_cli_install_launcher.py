import os
from click.testing import CliRunner

from lampkitctl import cli, launcher


def _fake_console(tmp_path):
    path = tmp_path / "venv/bin/lampkitctl"
    path.parent.mkdir(parents=True)
    path.write_text("#!/bin/bash\n")
    os.chmod(path, 0o755)
    return path


def test_cli_install_launcher(monkeypatch, tmp_path):
    console = _fake_console(tmp_path)
    monkeypatch.setattr(launcher, "resolve_self_executable", lambda: str(console))
    called = {}
    monkeypatch.setattr(
        cli, "maybe_reexec_with_sudo", lambda *a, **k: called.setdefault("called", True)
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["install-launcher", "--dir", str(tmp_path / "bin")]
    )
    assert result.exit_code == 0
    assert called["called"] is True
    assert (tmp_path / "bin/lampkitctl").exists()


def test_cli_uninstall_launcher(monkeypatch, tmp_path):
    path = tmp_path / "bin/lampkitctl"
    path.parent.mkdir(parents=True)
    path.write_text("echo")
    os.chmod(path, 0o755)
    called = {}
    monkeypatch.setattr(
        cli, "maybe_reexec_with_sudo", lambda *a, **k: called.setdefault("called", True)
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["uninstall-launcher", "--dir", str(path.parent)]
    )
    assert result.exit_code == 0
    assert called["called"] is True
    assert not path.exists()
