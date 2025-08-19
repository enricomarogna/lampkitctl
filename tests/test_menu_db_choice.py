from lampkitctl import menu
from types import SimpleNamespace


def test_menu_db_choice(monkeypatch):
    sequence = iter(["Install LAMP server", "MariaDB", "Exit"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: True)
    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(menu, "resolve_self_executable", lambda: "/venv/lampkitctl")

    called = {}

    def fake_run(args, **kwargs):
        called["args"] = args
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(menu.subprocess, "run", fake_run)

    menu.run_menu(dry_run=True)
    assert called["args"] == [
        "/venv/lampkitctl",
        "install-lamp",
        "--db-engine",
        "mariadb",
        "--wait-apt-lock",
        "120",
        "--set-db-root-pass",
    ]
