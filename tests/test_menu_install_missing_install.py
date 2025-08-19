from types import SimpleNamespace

from lampkitctl import menu
from lampkitctl.packages import PkgStatus


def test_menu_install_missing_install(monkeypatch):
    calls = []

    monkeypatch.setattr(menu, "detect_pkg_status", lambda pkgs: PkgStatus(["apache2"], [], ["mysql-server"]))
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(menu.preflight, "checks_for", lambda *a, **k: [])
    monkeypatch.setattr(menu.preflight_locks, "wait_for_lock", lambda n: SimpleNamespace(locked=False))
    monkeypatch.setattr(menu.preflight_locks, "detect_lock", lambda: SimpleNamespace(locked=False))
    monkeypatch.setattr(menu, "maybe_reexec_with_sudo", lambda *a, **k: None)

    monkeypatch.setattr(menu.system_ops, "compute_lamp_packages", lambda e: ["mysql-server", "apache2"])
    monkeypatch.setattr(menu.system_ops, "run_command", lambda cmd, dry_run: calls.append(cmd))

    def fake_install_or_update(engine, dry_run=False, refresh=False):
        calls.append(["apt-get", "install", "-y", "--no-install-recommends", "mysql-server", "apache2"])

    monkeypatch.setattr(menu.system_ops, "install_or_update_lamp", fake_install_or_update)
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: True)

    menu.install_lamp(db_engine="mysql", wait_apt_lock=0, dry_run=False)

    assert ["apt-get", "install", "-y", "--no-install-recommends", "mysql-server", "apache2"] in calls
