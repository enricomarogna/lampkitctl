from click.testing import CliRunner

from lampkitctl import cli, preflight


def test_install_lamp_preflight_fail(monkeypatch):
    monkeypatch.setattr(preflight, "is_root_or_sudo", lambda: False)
    monkeypatch.setattr(preflight, "has_cmd", lambda name: True)
    monkeypatch.setattr(preflight, "is_supported_os", lambda: True)
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--non-interactive", "install-lamp"])
    assert result.exit_code == 2
    assert "Preflight failed: install-lamp" in result.output


def test_install_lamp_preflight_pass(monkeypatch):
    monkeypatch.setattr(preflight, "is_root_or_sudo", lambda: True)
    monkeypatch.setattr(preflight, "has_cmd", lambda name: True)
    monkeypatch.setattr(preflight, "is_supported_os", lambda: True)
    monkeypatch.setattr(cli.system_ops, "check_service", lambda s: True)
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--non-interactive", "install-lamp"])
    assert result.exit_code == 0


def test_generate_ssl_missing_certbot(monkeypatch):
    def fake_has_cmd(name):
        return False if name == "certbot" else True

    monkeypatch.setattr(preflight, "has_cmd", fake_has_cmd)
    monkeypatch.setattr(preflight, "apache_paths_present", lambda: True)
    monkeypatch.setattr(preflight.Path, "exists", lambda self: True)
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--non-interactive", "generate-ssl", "example.com"],
    )
    assert result.exit_code == 2
    assert "certbot not installed" in result.output
