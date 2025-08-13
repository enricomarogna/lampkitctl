from lampkitctl import menu, preflight


def test_menu_install_lamp_blocking(monkeypatch, capsys):
    sequence = iter(["Install LAMP server", "Exit"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))
    monkeypatch.setattr(
        preflight,
        "is_root_or_sudo",
        lambda: preflight.CheckResult(False, "Root privileges required. Run with sudo."),
    )
    monkeypatch.setattr(
        preflight,
        "has_cmd",
        lambda name, msg=None, severity=preflight.Severity.BLOCKING: preflight.CheckResult(True, ""),
    )
    monkeypatch.setattr(
        preflight,
        "is_supported_os",
        lambda: preflight.CheckResult(True, ""),
    )
    calls = []
    monkeypatch.setattr(menu.system_ops, "install_service", lambda *a, **k: calls.append(a))
    menu.run_menu()
    captured = capsys.readouterr()
    assert "Preflight failed" in captured.err
    assert calls == []
    assert "Traceback" not in captured.err
