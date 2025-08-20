from types import SimpleNamespace

from lampkitctl import system_ops


def test_upgrade_core_dry_run(monkeypatch):
    cmds = []

    def fake_run(cmd, dry_run=False, **kwargs):
        cmds.append((cmd, dry_run))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(system_ops, "run_command", fake_run)
    monkeypatch.setattr(
        system_ops.preflight_locks, "wait_for_lock", lambda t: SimpleNamespace(locked=False)
    )
    monkeypatch.setattr(
        system_ops.preflight_locks, "detect_lock", lambda: SimpleNamespace(locked=False)
    )

    system_ops.upgrade_core_components("mysql", dry_run=True, wait_apt_lock=120)

    assert cmds[1][0][:3] == ["apt", "upgrade", "-y"]
    assert cmds[1][1] is True
