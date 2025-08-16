import sys

from lampkitctl import menu


def test_menu_install_lamp_blocking(monkeypatch, capsys):
    sequence = iter(["Install LAMP server", "Auto", "Exit"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: True)
    monkeypatch.setattr(menu, "_password", lambda m: "pw")

    def fake_run_cli(args, dry_run=False):
        print("Preflight failed", file=sys.stderr)
        return 1

    monkeypatch.setattr(menu, "_run_cli", fake_run_cli)

    menu.run_menu()
    captured = capsys.readouterr()
    assert "Preflight failed" in captured.err
