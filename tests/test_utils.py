import logging
import subprocess
from lampkitctl import utils


def test_run_command_dry_run(monkeypatch):
    called = False

    def fake_run(cmd, check, text):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    utils.run_command(["echo", "hi"], dry_run=True)
    assert not called


def test_run_command_executes(monkeypatch):
    recorded = {}

    def fake_run(cmd, check, text):
        recorded["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "out", "err")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = utils.run_command(["echo", "hi"], dry_run=False)
    assert recorded["cmd"] == ["echo", "hi"]
    assert result.returncode == 0


def test_prompt_confirm_yes(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert utils.prompt_confirm("?", default=False)


def test_prompt_confirm_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert utils.prompt_confirm("?", default=True)


def test_run_command_log_cmd(caplog):
    caplog.set_level(logging.INFO)
    utils.run_command(["echo", "secret"], dry_run=True, log_cmd=["echo", "***"])
    assert caplog.records[0].cmd == ["echo", "***"]


def test_setup_logging():
    utils.setup_logging()
    logger = logging.getLogger()
    assert logger.handlers
