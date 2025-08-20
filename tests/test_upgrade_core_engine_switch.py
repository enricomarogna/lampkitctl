from types import SimpleNamespace

from lampkitctl import system_ops


def test_upgrade_core_engine_switch(monkeypatch):
    cmds = []

    def fake_run(cmd, dry_run=False, **kwargs):
        cmds.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(system_ops, "run_command", fake_run)
    monkeypatch.setattr(
        system_ops.preflight_locks, "wait_for_lock", lambda t: SimpleNamespace(locked=False)
    )
    monkeypatch.setattr(
        system_ops.preflight_locks, "detect_lock", lambda: SimpleNamespace(locked=False)
    )

    system_ops.upgrade_core_components("mariadb", dry_run=True, wait_apt_lock=120)

    assert ["apt", "upgrade", "-y", "apache2", "mariadb-server", "php"] in cmds
    assert all("mysql-server" not in cmd for cmd in cmds if isinstance(cmd, list))
