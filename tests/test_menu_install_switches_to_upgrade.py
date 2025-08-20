from types import SimpleNamespace

from lampkitctl import menu


def test_menu_install_switches_to_upgrade(monkeypatch):
    sequence = iter(["Install LAMP server"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices=None: next(sequence))
    confirms = iter([True, True])
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: next(confirms))
    monkeypatch.setattr(menu, "detect_installed_db", lambda: "mysql")
    monkeypatch.setattr(menu, "is_installed", lambda pkg: True)
    monkeypatch.setattr(menu, "maybe_reexec_with_sudo", lambda *a, **k: None)
    cmds = []

    def fake_run(cmd, dry_run=False, **kwargs):
        cmds.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(menu.system_ops, "run_command", fake_run)
    monkeypatch.setattr(
        menu.system_ops.preflight_locks, "wait_for_lock", lambda t: SimpleNamespace(locked=False)
    )
    monkeypatch.setattr(
        menu.system_ops.preflight_locks, "detect_lock", lambda: SimpleNamespace(locked=False)
    )

    menu.run_menu(dry_run=True)

    assert ["apt", "upgrade", "-y", "apache2", "mysql-server", "php"] in cmds
    assert not any(cmd[:2] == ["apt-get", "install"] for cmd in cmds)
