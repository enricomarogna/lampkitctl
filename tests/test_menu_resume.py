import pytest

from lampkitctl import menu

def test_menu_install_lamp_execs_sudo(monkeypatch):
    captured = {}

    monkeypatch.setattr(menu, "resolve_self_executable", lambda: "/abs/path/to/lampkitctl")
    monkeypatch.setattr(menu.os, "geteuid", lambda: 1000)

    def fake_execvp(file, args):
        captured["cmd"] = args
        raise SystemExit()

    monkeypatch.setattr(menu.os, "execvp", fake_execvp)

    responses = iter(["Install LAMP server", "MySQL"])
    monkeypatch.setattr(menu, "_select", lambda message, choices: next(responses))

    with pytest.raises(SystemExit):
        menu.run_menu(dry_run=False)

    assert captured["cmd"] == [
        "sudo",
        "/abs/path/to/lampkitctl",
        "install-lamp",
        "--db-engine",
        "mysql",
    ]


def test_run_cli_root_calls_subprocess(monkeypatch):
    monkeypatch.setattr(menu, "resolve_self_executable", lambda: "/abs/path/to/lampkitctl")
    monkeypatch.setattr(menu.os, "geteuid", lambda: 0)
    called = {}

    def fake_call(args):
        called["args"] = args
        return 0

    monkeypatch.setattr(menu.subprocess, "call", fake_call)

    rc = menu._run_cli(["install-lamp", "--db-engine", "mysql"], dry_run=False)

    assert rc == 0
    assert called["args"] == [
        "/abs/path/to/lampkitctl",
        "install-lamp",
        "--db-engine",
        "mysql",
    ]
