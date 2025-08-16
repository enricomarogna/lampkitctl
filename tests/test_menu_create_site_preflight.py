from lampkitctl import menu, preflight


def test_create_site_preflight_blocks_prompts(monkeypatch):
    monkeypatch.setattr(menu.preflight, "is_apache_installed", lambda: preflight.CheckResult(False, "no apache"))
    monkeypatch.setattr(menu.preflight, "apache_paths_present", lambda: preflight.CheckResult(False, "no paths"))
    monkeypatch.setattr(menu.preflight, "is_mysql_installed", lambda: preflight.CheckResult(False, "no mysql"))
    monkeypatch.setattr(menu.preflight, "is_php_installed", lambda: preflight.CheckResult(False, "no php"))

    confirms = []
    texts = []

    monkeypatch.setattr(menu, "_confirm", lambda m, default=False: confirms.append(m) or False)
    monkeypatch.setattr(menu, "_text", lambda m, default="": texts.append(m) or "")

    menu._create_site_flow(dry_run=True)

    assert texts == []
    assert confirms == ["Run install-lamp now?"]
