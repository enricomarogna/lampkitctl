from click.testing import CliRunner

from lampkitctl import cli, preflight


def test_install_lamp_preflight_fail(monkeypatch):
    monkeypatch.setattr(
        preflight,
        "is_root_or_sudo",
        lambda: preflight.CheckResult(False, "root"),
    )
    monkeypatch.setattr(
        preflight,
        "has_cmd",
        lambda name, msg=None, severity=preflight.Severity.BLOCKING: preflight.CheckResult(True, name),
    )
    monkeypatch.setattr(
        preflight, "is_supported_os", lambda: preflight.CheckResult(True, "")
    )
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--non-interactive", "install-lamp"])
    assert result.exit_code == 2
    assert "Preflight failed" in result.output


def test_install_lamp_preflight_pass(monkeypatch):
    monkeypatch.setattr(
        preflight,
        "is_root_or_sudo",
        lambda: preflight.CheckResult(True, "root"),
    )
    monkeypatch.setattr(
        preflight,
        "has_cmd",
        lambda name, msg=None, severity=preflight.Severity.BLOCKING: preflight.CheckResult(True, name),
    )
    monkeypatch.setattr(
        preflight, "is_supported_os", lambda: preflight.CheckResult(True, "")
    )
    monkeypatch.setattr(cli.system_ops, "check_service", lambda s: True)
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--non-interactive", "install-lamp"])
    assert result.exit_code == 0


def test_generate_ssl_missing_certbot(monkeypatch):
    def fake_has_cmd(name, msg=None, severity=preflight.Severity.BLOCKING):
        ok = False if name == "certbot" else True
        return preflight.CheckResult(ok, msg or name)

    monkeypatch.setattr(preflight, "has_cmd", fake_has_cmd)
    monkeypatch.setattr(
        preflight, "apache_paths_present", lambda: preflight.CheckResult(True, "")
    )
    monkeypatch.setattr(preflight.Path, "exists", lambda self: True)
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--non-interactive", "generate-ssl", "example.com"],
    )
    assert result.exit_code == 2
    assert "certbot not installed" in result.output
