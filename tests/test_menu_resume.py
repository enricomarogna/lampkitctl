import pytest

from lampkitctl import menu
from types import SimpleNamespace


def test_menu_install_lamp_uses_sudo(monkeypatch):
    captured = {}

    monkeypatch.setattr(menu, "resolve_self_executable", lambda: "/abs/path/to/lampkitctl")
    monkeypatch.setattr(menu.os, "geteuid", lambda: 1000)

    def fake_run(args, **kwargs):
        captured["args"] = args
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(menu.subprocess, "run", fake_run)

    responses = iter(["Install LAMP server", "MySQL"])
    monkeypatch.setattr(menu, "_select", lambda message, choices: next(responses))
    monkeypatch.setattr(menu, "_confirm", lambda message, default=True: True)

    menu.run_menu(dry_run=False)

    assert captured["args"] == [
        "sudo",
        "/abs/path/to/lampkitctl",
        "install-lamp",
        "--db-engine",
        "mysql",
        "--wait-apt-lock",
        "120",
        "--set-db-root-pass",
    ]


def test_run_cli_root_calls_subprocess(monkeypatch):
    monkeypatch.setattr(menu, "resolve_self_executable", lambda: "/abs/path/to/lampkitctl")
    monkeypatch.setattr(menu.os, "geteuid", lambda: 0)
    called = {}

    def fake_run(args, **kwargs):
        called["args"] = args
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(menu.subprocess, "run", fake_run)

    rc = menu._run_cli([
        "install-lamp",
        "--db-engine",
        "mysql",
        "--wait-apt-lock",
        "120",
    ], dry_run=False)

    assert rc == 0
    assert called["args"] == [
        "/abs/path/to/lampkitctl",
        "install-lamp",
        "--db-engine",
        "mysql",
        "--wait-apt-lock",
        "120",
    ]
