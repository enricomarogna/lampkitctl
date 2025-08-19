from types import SimpleNamespace
from lampkitctl import menu, apache_vhosts, db_introspect


def make_vhost(domain, docroot):
    return apache_vhosts.VHost(domain, docroot, "/etc/apache2/sites-available/a.conf", False)


def test_db_picker_preselects_wp_db(monkeypatch):
    vhost = make_vhost("a.com", "/a")
    monkeypatch.setattr(menu, "_choose_site", lambda: vhost)
    monkeypatch.setattr(
        menu.db_introspect,
        "list_databases",
        lambda: db_introspect.DBList(["wpdb", "other"]),
    )
    monkeypatch.setattr(
        menu.db_introspect,
        "parse_wp_config",
        lambda path: db_introspect.WPConfig("wpdb", None, None, None),
    )

    def fake_select(message=None, choices=None, default=None):
        fake_select.default = default
        class R:
            def execute(self):
                return default
        return R()

    menu.inquirer = SimpleNamespace(select=fake_select, text=lambda **k: None)
    monkeypatch.setattr(menu, "_text", lambda *a, **k: "dbuser")
    monkeypatch.setattr(menu, "_confirm", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(menu, "_run_cli", lambda args, dry_run=False: calls.append(args) or 0)
    menu._uninstall_site_flow(dry_run=False)
    assert calls == [[
        "uninstall-site",
        "a.com",
        "--doc-root",
        "/a",
        "--db-name",
        "wpdb",
        "--db-user",
        "dbuser",
    ]]
    assert fake_select.default == "wpdb"


def test_db_picker_warns_missing_wp_db(monkeypatch):
    vhost = make_vhost("a.com", "/a")
    monkeypatch.setattr(menu, "_choose_site", lambda: vhost)
    monkeypatch.setattr(
        menu.db_introspect,
        "list_databases",
        lambda: db_introspect.DBList(["alpha", "beta"]),
    )
    monkeypatch.setattr(
        menu.db_introspect,
        "parse_wp_config",
        lambda path: db_introspect.WPConfig("missing", None, None, None),
    )
    warns = []
    monkeypatch.setattr(menu, "echo_warn", lambda msg: warns.append(msg))

    def fake_select(message=None, choices=None, default=None):
        fake_select.default = default
        class R:
            def execute(self):
                return default
        return R()

    menu.inquirer = SimpleNamespace(select=fake_select, text=lambda **k: None)
    monkeypatch.setattr(menu, "_text", lambda *a, **k: "dbuser")
    monkeypatch.setattr(menu, "_confirm", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(menu, "_run_cli", lambda args, dry_run=False: calls.append(args) or 0)
    menu._uninstall_site_flow(dry_run=False)
    assert calls == [[
        "uninstall-site",
        "a.com",
        "--doc-root",
        "/a",
        "--db-name",
        "alpha",
        "--db-user",
        "dbuser",
    ]]
    assert fake_select.default == "alpha"
    assert warns == ["DB from wp-config.php not found on server: missing"]
