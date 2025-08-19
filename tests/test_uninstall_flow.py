from types import SimpleNamespace

from lampkitctl import menu, utils


def _vhost():
    return SimpleNamespace(domain="ex.com", docroot="/var/www/ex.com")


def test_uninstall_never_prompts_install(monkeypatch, capsys):
    monkeypatch.setattr(menu, "_choose_site", _vhost)
    monkeypatch.setattr(menu, "_db_picker_with_fallbacks", lambda d: "db")
    monkeypatch.setattr(menu, "_db_user_picker_with_fallbacks", lambda d: "user")
    monkeypatch.setattr(menu, "ask_confirm", lambda *a, **k: True)

    calls = []

    def fake_run(args, dry_run=False):
        calls.append(args)
        return 1  # simulate failure

    monkeypatch.setattr(menu, "_run_cli", fake_run)
    menu._uninstall_site_flow(dry_run=False)
    assert calls == [[
        "uninstall-site",
        "ex.com",
        "--doc-root",
        "/var/www/ex.com",
        "--db-name",
        "db",
        "--db-user",
        "user",
    ]]
    assert all("install-lamp" not in c for c in calls)
    out = capsys.readouterr().out
    assert "Run install-lamp now?" not in out


def test_uninstall_confirm_boolean(monkeypatch):
    monkeypatch.setattr(menu, "_choose_site", _vhost)
    monkeypatch.setattr(menu, "_db_picker_with_fallbacks", lambda d: "db")
    monkeypatch.setattr(menu, "_db_user_picker_with_fallbacks", lambda d: "user")

    responses = iter([True, False])

    class Dummy:
        def execute(self):
            return next(responses)

    monkeypatch.setattr(utils, "inquirer", SimpleNamespace(confirm=lambda **k: Dummy()))
    called = []
    monkeypatch.setattr(menu, "_run_cli", lambda args, dry_run=False: called.append(args))
    menu._uninstall_site_flow(dry_run=False)
    assert not called
