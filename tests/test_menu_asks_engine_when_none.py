from lampkitctl import menu
from lampkitctl.packages import PkgStatus


def test_menu_prompts_when_no_engine(monkeypatch):
    # No engine detected
    monkeypatch.setattr(menu, "detect_installed_db", lambda: None)
    monkeypatch.setattr(menu.system_ops, "compute_lamp_packages", lambda e: [e])
    monkeypatch.setattr(menu, "detect_pkg_status", lambda pkgs: PkgStatus(["apache2"], [], []))

    sequence = iter(["Install LAMP server", "MySQL"])

    def fake_select(msg, choices):
        return next(sequence)

    monkeypatch.setattr(menu, "_select", fake_select)
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: False)
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    chosen = {}

    def fake_install_lamp(db_engine: str, **k):
        chosen["engine"] = db_engine
        return db_engine

    monkeypatch.setattr(menu, "install_lamp", fake_install_lamp)

    menu.run_menu(dry_run=True)
    assert chosen["engine"] == "mysql"
