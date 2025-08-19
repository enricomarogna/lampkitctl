from types import SimpleNamespace
from lampkitctl import menu, db_introspect, auth_cache


def test_db_list_auth_flow(monkeypatch):
    monkeypatch.setattr(menu.db_introspect, "parse_wp_config", lambda path: None)
    auth_cache.clear()

    calls = []

    def fake_list(password: str | None = None):
        calls.append(password)
        if password == "pw":
            return ["alpha", "beta"]
        raise db_introspect.DBListError("fail")

    monkeypatch.setattr(menu.dbi, "list_databases", fake_list)

    secrets = []

    def fake_secret(message):
        secrets.append(message)

        class R:
            def execute(self):
                return "pw"

        return R()

    def fake_select(message=None, choices=None, default=None):
        class R:
            def execute(self):
                return choices[0]["value"]

        return R()

    menu.inquirer = SimpleNamespace(secret=fake_secret, select=fake_select, text=lambda **k: None)

    dblist = menu._db_picker_with_fallbacks("/tmp")
    assert dblist == "alpha"
    assert secrets == ["Database root password:"]
    assert calls == [None, "pw"]
