import logging
from lampkitctl import wp_ops


def test_set_permissions(monkeypatch) -> None:
    """Ensure file permissions are set via three commands.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    calls = []

    def fake_run(cmd, dry_run):
        calls.append(cmd)

    monkeypatch.setattr(wp_ops, "run_command", fake_run)
    wp_ops.set_permissions("/var/www/site", dry_run=True)
    assert len(calls) == 3


def test_install_wordpress_dry_run(caplog) -> None:
    """Check that WordPress installation logs configuration in dry run.

    Args:
        caplog (pytest.LogCaptureFixture): Fixture to capture log records.
    """
    caplog.set_level(logging.INFO)
    wp_ops.install_wordpress(
        "/tmp", "db", "user", "pw", dry_run=True
    )
    assert "configure_wp" in caplog.text


def test_download_wordpress(monkeypatch) -> None:
    """Verify the download command is executed.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    calls = []

    def fake_run(cmd, dry_run):
        calls.append(cmd)

    monkeypatch.setattr(wp_ops, "run_command", fake_run)
    wp_ops.download_wordpress("/tmp", dry_run=True)
    assert calls[0][0] == "wget"
