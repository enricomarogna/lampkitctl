from lampkitctl import menu, preflight, apache_vhosts


def make_vhost(domain, docroot, ssl=False):
    return apache_vhosts.VHost(domain, docroot, f"/etc/apache2/sites-available/{domain}.conf", ssl)


def test_wp_permissions_uses_selected_site(monkeypatch):
    vhosts = [make_vhost("a.com", "/a"), make_vhost("b.com", "/b")]
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: vhosts)
    monkeypatch.setattr(menu, "inquirer", None)
    monkeypatch.setattr(menu.preflight, "is_apache_installed", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "apache_paths_present", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "path_exists", lambda p: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "is_wordpress_dir", lambda p: preflight.CheckResult(True, ""))
    calls = []
    monkeypatch.setattr(menu, "_run_cli", lambda args, dry_run=False: calls.append(args) or 0)
    inputs = iter(["2"])  # select second site
    monkeypatch.setattr(menu, "input", lambda _: next(inputs), raising=False)
    monkeypatch.setattr(menu, "_text", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    menu._wp_permissions_flow(dry_run=False)
    assert calls == [["wp-permissions", "/b"]]


def test_uninstall_site_uses_selected_domain(monkeypatch):
    vhosts = [make_vhost("a.com", "/a"), make_vhost("b.com", "/b")]
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: vhosts)
    monkeypatch.setattr(menu, "inquirer", None)
    inputs = iter(["1"])  # select first site
    monkeypatch.setattr(menu, "input", lambda _: next(inputs), raising=False)
    monkeypatch.setattr(menu, "_choose_database", lambda doc_root: "dbname")
    texts = iter(["dbuser"])
    monkeypatch.setattr(menu, "_text", lambda *a, **k: next(texts))
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
        "dbname",
        "--db-user",
        "dbuser",
    ]]


def test_generate_ssl_uses_selected_domain(monkeypatch):
    vhosts = [make_vhost("a.com", "/a"), make_vhost("b.com", "/b", ssl=False)]
    monkeypatch.setattr(menu.apache_vhosts, "list_vhosts", lambda: vhosts)
    monkeypatch.setattr(menu, "inquirer", None)
    inputs = iter(["2"])  # select second site
    monkeypatch.setattr(menu, "input", lambda _: next(inputs), raising=False)
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(menu.preflight, "checks_for", lambda *a, **k: [])
    monkeypatch.setattr(menu, "_text", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    monkeypatch.setattr(menu, "_confirm", lambda *a, **k: True)
    calls = []
    monkeypatch.setattr(menu, "_run_cli", lambda args, dry_run=False: calls.append(args) or 0)
    menu._generate_ssl_flow(dry_run=False)
    assert calls == [["generate-ssl", "b.com"]]
