from lampkitctl import menu
from lampkitctl.packages import PkgStatus


def test_menu_skip_engine_when_installed(monkeypatch, capsys):
    # Detection returns mariadb and packages are present (no missing)
    monkeypatch.setattr(menu, "detect_installed_db", lambda: "mariadb")
    monkeypatch.setattr(menu.system_ops, "compute_lamp_packages", lambda e: [e])
    monkeypatch.setattr(menu, "detect_pkg_status", lambda pkgs: PkgStatus([], [], pkgs))

    sequence = iter(["Install LAMP server"])

    def fake_select(msg, choices):
        assert msg == "Main > Choose an option"
        return next(sequence)

    monkeypatch.setattr(menu, "_select", fake_select)
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: False)
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(menu, "install_lamp", lambda **k: "mariadb")

    menu.run_menu(dry_run=True)
    captured = capsys.readouterr().out
    assert "DB engine: MariaDB (auto-detected)" in captured
