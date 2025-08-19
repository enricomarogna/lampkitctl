from lampkitctl import menu, utils


def test_no_sites_found_color(monkeypatch):
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: [])
    calls = []

    def fake_secho(msg, fg=None, bold=None, **kwargs):
        calls.append((msg, fg, bold))

    monkeypatch.setattr(utils.click, "secho", fake_secho)
    menu._uninstall_site_flow(dry_run=True)
    assert calls[0] == ("No sites found", "red", True)


def test_no_sites_for_ssl_color(monkeypatch):
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: [])
    calls = []

    def fake_secho(msg, fg=None, bold=None, **kwargs):
        calls.append((msg, fg, bold))

    monkeypatch.setattr(utils.click, "secho", fake_secho)
    menu._generate_ssl_flow(dry_run=True)
    assert calls[0] == ("No sites found", "red", True)
