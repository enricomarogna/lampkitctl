from lampkitctl import menu, apache_vhosts


def make_vhost(domain, docroot, ssl=False):
    return apache_vhosts.VHost(domain, docroot, f"/etc/apache2/sites-available/{domain}.conf", ssl)


def test_menu_site_picker_simple_list(monkeypatch, capsys):
    vhosts = [make_vhost("a.com", "/var/www/a"), make_vhost("b.net", "/var/www/b")]
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: vhosts)
    monkeypatch.setattr(menu, "inquirer", None)
    inputs = iter(["1"])
    monkeypatch.setattr(menu, "input", lambda _: next(inputs), raising=False)

    sel = menu._choose_site()
    out = capsys.readouterr().out

    lines = out.splitlines()
    assert lines[0] == "Select a site"
    assert lines[1] == "1) a.com | /var/www/a"
    assert lines[2] == "2) b.net | /var/www/b"
    assert lines[3] == "3) Custom..."
    assert sel == vhosts[0]


def test_menu_site_picker_inquirer_choices(monkeypatch):
    vhosts = [make_vhost("a.com", "/var/www/a")]
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: vhosts)
    captured: dict[str, list] = {}

    class DummySelect:
        def __init__(self, *, choices=None, message=None):
            captured["choices"] = choices

        def execute(self):
            return ("a.com", "/var/www/a")

    class DummyInquirer:
        def select(self, **kwargs):
            return DummySelect(**kwargs)

    monkeypatch.setattr(menu, "inquirer", DummyInquirer())
    sel = menu._choose_site()
    assert sel == vhosts[0]
    choices = captured["choices"]
    assert len(choices) == 2
    assert choices[0]["name"] == "a.com | /var/www/a"
    assert choices[1]["name"] == "Custom..."
