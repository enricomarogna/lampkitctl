from lampkitctl import menu, packages


def test_menu_db_choice(monkeypatch):
    sequence = iter(["Install LAMP server", "MariaDB", "Exit"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    calls = []

    def fake_install(pref, dry_run=False):
        calls.append(pref)
        return packages.Engine("mariadb", "mariadb-server", "mariadb-client", "mariadb")

    monkeypatch.setattr(menu.system_ops, "install_lamp_stack", fake_install)
    menu.run_menu(dry_run=True)
    assert calls == ["mariadb"]
