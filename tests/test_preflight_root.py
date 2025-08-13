from click.testing import CliRunner

from lampkitctl import cli, preflight


def test_install_lamp_requires_root(monkeypatch):
    monkeypatch.setattr(
        preflight,
        "is_root_or_sudo",
        lambda: preflight.CheckResult(False, "Root privileges required. Run with sudo."),
    )
    monkeypatch.setattr(
        preflight,
        "has_cmd",
        lambda name, msg=None, severity=preflight.Severity.BLOCKING: preflight.CheckResult(True, ""),
    )
    monkeypatch.setattr(
        preflight, "is_supported_os", lambda: preflight.CheckResult(True, "")
    )
    calls = []
    monkeypatch.setattr(cli.system_ops, "install_service", lambda *a, **k: calls.append(a))
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["install-lamp"])
    assert result.exit_code == 2
    assert "Root privileges required" in result.output
    assert calls == []
