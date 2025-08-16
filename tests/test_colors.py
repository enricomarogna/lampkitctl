from lampkitctl import menu, utils


def test_no_sites_found_color(monkeypatch):
    monkeypatch.setattr(menu, "list_installed_sites", lambda: [])
    calls = []

    def fake_secho(msg, fg=None, bold=None, **kwargs):
        calls.append((msg, fg, bold))

    monkeypatch.setattr(utils.click, "secho", fake_secho)
    menu._uninstall_site_flow(dry_run=True)
    assert calls[0] == ("No sites found", "red", True)


def test_no_domains_available_color(monkeypatch):
    monkeypatch.setattr(menu, "list_installed_sites", lambda: [])
    calls = []

    def fake_secho(msg, fg=None, bold=None, **kwargs):
        calls.append((msg, fg, bold))

    monkeypatch.setattr(utils.click, "secho", fake_secho)
    menu._generate_ssl_flow(dry_run=True)
    assert calls[0] == ("No domains available", "red", True)
