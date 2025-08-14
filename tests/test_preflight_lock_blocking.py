import subprocess

from click.testing import CliRunner

from lampkitctl import cli, preflight


class Proc:
    def __init__(self, stdout: str):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = 0


def test_apt_lock_blocks_install(monkeypatch):
    def fake_run(cmd, capture_output=True, text=True):
        return Proc("apt-get")

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    monkeypatch.setattr(cli.system_ops, "install_lamp_stack", lambda *a, **k: None)
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["install-lamp"])
    assert result.exit_code == 2
    assert "Preflight failed: package manager is busy" in result.output

