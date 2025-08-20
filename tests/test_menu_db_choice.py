from lampkitctl import menu


def test_menu_db_choice(monkeypatch):
    sequence = iter(["Install LAMP server", "MariaDB"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: True)
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)

    called = {}

    def fake_install_lamp(db_engine: str, wait_apt_lock: int, dry_run: bool, **kwargs):
        called["engine"] = db_engine
        return "mariadb"

    monkeypatch.setattr(menu, "install_lamp", fake_install_lamp)
    monkeypatch.setattr(menu, "ensure_db_root_password", lambda: "pw")
    monkeypatch.setattr(menu.db_ops, "set_root_password", lambda *a, **k: None)

    menu.run_menu(dry_run=True)
    assert called["engine"] == "mariadb"
