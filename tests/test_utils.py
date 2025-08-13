import logging
import subprocess
from lampkitctl import utils


def test_run_command_dry_run(monkeypatch) -> None:
    """Ensure dry-run mode does not execute the command.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    called = False

    def fake_run(cmd, **kwargs):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    utils.run_command(["echo", "hi"], dry_run=True)
    assert not called


def test_run_command_executes(monkeypatch) -> None:
    """Verify that the command executes when not in dry-run mode.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    recorded = {}

    def fake_run(cmd, **kwargs):
        recorded["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "out", "err")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = utils.run_command(["echo", "hi"], dry_run=False)
    assert recorded["cmd"] == ["echo", "hi"]
    assert result.returncode == 0


def test_prompt_confirm_yes(monkeypatch) -> None:
    """Confirm that affirmative input returns ``True``.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching builtins.
    """
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert utils.prompt_confirm("?", default=False)


def test_prompt_confirm_default(monkeypatch) -> None:
    """Ensure default value is returned when input is empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching builtins.
    """
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert utils.prompt_confirm("?", default=True)


def test_run_command_log_cmd(caplog) -> None:
    """Verify that an alternative command representation is logged.

    Args:
        caplog (pytest.LogCaptureFixture): Fixture to capture log records.
    """
    caplog.set_level(logging.INFO)
    utils.run_command(["echo", "secret"], dry_run=True, log_cmd=["echo", "***"])
    assert caplog.records[0].cmd == ["echo", "***"]


def test_setup_logging() -> None:
    """Check that logging is configured with at least one handler."""
    utils.setup_logging()
    logger = logging.getLogger()
    assert logger.handlers
