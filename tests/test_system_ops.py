import logging
from lampkitctl import system_ops


def test_create_virtualhost(tmp_path) -> None:
    """Ensure virtual host configuration files are created.

    Args:
        tmp_path (pathlib.Path): Temporary directory provided by pytest.
    """
    conf_dir = tmp_path / "sites"
    conf_dir.mkdir()
    conf_path = system_ops.create_virtualhost(
        "example.com", "/var/www/example", sites_available=str(conf_dir)
    )
    assert conf_path.exists()


def test_list_sites(tmp_path) -> None:
    """Verify detection of existing virtual host configurations.

    Args:
        tmp_path (pathlib.Path): Temporary directory provided by pytest.
    """
    conf = tmp_path / "example.com.conf"
    conf.write_text("DocumentRoot /var/www/example")
    sites = system_ops.list_sites(str(tmp_path))
    assert sites[0]["domain"] == "example.com"


def test_remove_virtualhost_dry_run(caplog) -> None:
    """Check that removal is logged during a dry run.

    Args:
        caplog (pytest.LogCaptureFixture): Fixture to capture log records.
    """
    caplog.set_level(logging.INFO)
    system_ops.remove_virtualhost("nosite", sites_available="/tmp", dry_run=True)
    assert "remove_virtualhost" in caplog.text


def test_install_service(monkeypatch) -> None:
    """Validate system service installation command.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    calls = []
    monkeypatch.setattr(system_ops, "run_command", lambda cmd, dry_run: calls.append(cmd))
    system_ops.install_service("apache2", dry_run=True)
    assert calls[1] == ["apt-get", "install", "-y", "apache2"]


def test_add_and_remove_host_entry(tmp_path) -> None:
    """Ensure host entries can be added and removed.

    Args:
        tmp_path (pathlib.Path): Temporary directory provided by pytest.
    """
    hosts = tmp_path / "hosts"
    system_ops.add_host_entry("example.com", hosts_file=str(hosts))
    assert "example.com" in hosts.read_text()
    system_ops.remove_host_entry("example.com", hosts_file=str(hosts))
    assert "example.com" not in hosts.read_text()


def test_enable_site(monkeypatch) -> None:
    """Verify enabling a site invokes the correct command.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
    """
    calls = []
    monkeypatch.setattr(system_ops, "run_command", lambda cmd, dry_run: calls.append(cmd))
    system_ops.enable_site("example.com", dry_run=True)
    assert calls[0][0] == "a2ensite"


def test_create_web_directory(monkeypatch, tmp_path) -> None:
    """Ensure web directories are created as expected.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture for patching objects.
        tmp_path (pathlib.Path): Temporary directory provided by pytest.
    """
    calls = []
    monkeypatch.setattr(system_ops, "run_command", lambda cmd, dry_run: calls.append(cmd))
    system_ops.create_web_directory(str(tmp_path / "web"), dry_run=True)
    assert calls[0][0] == "mkdir"
