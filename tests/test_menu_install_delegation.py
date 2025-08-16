from lampkitctl import menu


def test_menu_delegates_db_password(monkeypatch):
    calls = {}

    sequence = iter(["Install LAMP server", "MySQL", "Exit"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))

    confirms = iter([True, True])
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: next(confirms))

    def fake_run(args, dry_run=False):
        calls["args"] = args
        return 0

    monkeypatch.setattr(menu, "_run_cli", fake_run)
    monkeypatch.setattr(menu, "_password", lambda m: (_ for _ in ()).throw(AssertionError))

    menu.run_menu(dry_run=False)
    assert calls["args"] == [
        "install-lamp",
        "--db-engine",
        "mysql",
        "--wait-apt-lock",
        "120",
        "--set-db-root-pass",
    ]
