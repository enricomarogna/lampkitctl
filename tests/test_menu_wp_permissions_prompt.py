from lampkitctl import menu, preflight


def test_wp_permissions_prompt_handles_defaults(monkeypatch):
    monkeypatch.setattr(menu.preflight, "is_apache_installed", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "apache_paths_present", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu, "_text", lambda m, default="": "")
    # Should exit without error even if empty string is returned
    menu._wp_permissions_flow(dry_run=True)


def test_wp_permissions_invalid_path_reprompt(monkeypatch, capsys):
    responses = iter(["/bad", "/good"])
    monkeypatch.setattr(menu, "_text", lambda m, default="": next(responses))

    def fake_exists(path):
        return preflight.CheckResult(path == "/good", "missing")

    def fake_wp(path):
        return preflight.CheckResult(path == "/good", "not wp")

    monkeypatch.setattr(menu.preflight, "is_apache_installed", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "apache_paths_present", lambda: preflight.CheckResult(True, ""))
    monkeypatch.setattr(menu.preflight, "path_exists", fake_exists)
    monkeypatch.setattr(menu.preflight, "is_wordpress_dir", fake_wp)

    calls = []
    monkeypatch.setattr(menu, "_run_cli", lambda args, dry_run=False: calls.append(args) or 0)

    menu._wp_permissions_flow(dry_run=False)

    out = capsys.readouterr().out
    assert "missing" in out or "not wp" in out
    assert calls == [["wp-permissions", "/good"]]
