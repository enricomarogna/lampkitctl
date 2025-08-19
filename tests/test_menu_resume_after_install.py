from lampkitctl import menu, preflight


def test_resume_after_install(monkeypatch):
    calls = []

    def fake_run_cli(args, dry_run=False):
        calls.append(list(args))
        if args[0] == "create-site" and len(calls) == 1:
            return 1  # simulate preflight failure
        return 0

    monkeypatch.setattr(menu, "_run_cli", fake_run_cli)
    monkeypatch.setattr(menu, "install_lamp", lambda **k: "mysql")
    monkeypatch.setattr(menu, "ensure_db_root_password", lambda: "pw")
    monkeypatch.setattr(menu.db_ops, "set_root_password", lambda *a, **k: None)
    monkeypatch.setattr(menu.preflight, "is_apache_installed", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "apache_paths_present", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "is_mysql_installed", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "is_php_installed", lambda: preflight.CheckResult(True, ""))
    select_iter = iter(["Create a site", "Exit"])
    text_iter = iter(["example.com", "/var/www/example", "db", "user"])

    monkeypatch.setattr(menu, "_select", lambda m, c: next(select_iter))
    monkeypatch.setattr(menu, "_text", lambda m, default="": next(text_iter))
    monkeypatch.setattr(menu, "_password", lambda m: "pw")

    def fake_confirm(message, default=False):
        return "install-lamp" in message

    monkeypatch.setattr(menu, "_confirm", fake_confirm)

    menu.run_menu(dry_run=False)

    assert calls[0][0] == "create-site"
    assert calls[1][0] == "install-lamp"
    assert calls[2][0] == "create-site"
