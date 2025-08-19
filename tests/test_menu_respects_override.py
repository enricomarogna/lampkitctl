from types import SimpleNamespace

from lampkitctl import menu
from lampkitctl.packages import PkgStatus


def test_menu_respects_db_engine_override(monkeypatch):
    # ensure system_ops.detect_db_engine not called when override supplied
    def fail_detect(preferred):  # pragma: no cover - should not be called
        raise AssertionError("override not respected")

    monkeypatch.setattr(menu.system_ops, "detect_db_engine", fail_detect)
    monkeypatch.setattr(menu.system_ops, "compute_lamp_packages", lambda e: [e])
    monkeypatch.setattr(menu.system_ops, "run_command", lambda *a, **k: None)
    monkeypatch.setattr(menu.system_ops, "install_or_update_lamp", lambda *a, **k: None)

    monkeypatch.setattr(menu, "detect_pkg_status", lambda pkgs: PkgStatus([], [], pkgs))
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(menu.preflight, "checks_for", lambda *a, **k: [])
    monkeypatch.setattr(menu.preflight_locks, "wait_for_lock", lambda n: SimpleNamespace(locked=False))
    monkeypatch.setattr(menu.preflight_locks, "detect_lock", lambda: SimpleNamespace(locked=False))
    monkeypatch.setattr(menu, "maybe_reexec_with_sudo", lambda *a, **k: None)
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: True)

    eng = menu.install_lamp(db_engine="mysql", wait_apt_lock=0, dry_run=True)
    assert eng == "mysql"
