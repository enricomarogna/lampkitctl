from types import SimpleNamespace

from lampkitctl import menu


def test_menu_install_missing_installs(monkeypatch):
    sequence = iter(["Install LAMP server"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices=None: next(sequence))
    confirms = iter([True, False])
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: next(confirms))
    monkeypatch.setattr(menu, "detect_installed_db", lambda: "mysql")

    def fake_is_installed(pkg: str) -> bool:
        return pkg != "php"

    monkeypatch.setattr(menu, "is_installed", fake_is_installed)

    called = {}

    def fake_install_lamp(db_engine, wait_apt_lock, dry_run, autodetected, show_engine):
        called["install"] = True
        return "mysql"

    monkeypatch.setattr(menu, "install_lamp", fake_install_lamp)
    monkeypatch.setattr(menu.system_ops, "upgrade_core_components", lambda *a, **k: called.update({"upgrade": True}))

    menu.run_menu(dry_run=True)

    assert called.get("install")
    assert "upgrade" not in called
