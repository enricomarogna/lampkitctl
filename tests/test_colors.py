from lampkitctl import menu


def test_no_sites_found_color(monkeypatch):
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: [])
    calls = []

    def fake_secho(msg, fg=None, bold=None, **kwargs):
        calls.append((msg, fg, bold))

    monkeypatch.setattr(menu, "secho", fake_secho)
    menu._uninstall_site_flow(dry_run=True)
    assert calls[0][:2] == ("No sites found", "red")


def test_no_sites_for_ssl_color(monkeypatch):
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: [])
    calls = []

    def fake_secho(msg, fg=None, bold=None, **kwargs):
        calls.append((msg, fg, bold))

    monkeypatch.setattr(menu, "secho", fake_secho)
    menu._generate_ssl_flow(dry_run=True)
    assert calls[0][:2] == ("No sites found", "red")
