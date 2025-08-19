from types import SimpleNamespace
from lampkitctl import menu, db_introspect
from types import SimpleNamespace


def test_db_picker_prefills_from_wp_config(monkeypatch):
    monkeypatch.setattr(menu.dbi, "list_databases", lambda password=None: (_ for _ in ()).throw(Exception("fail")))
    monkeypatch.setattr(menu.dbi, "list_databases_with_sudo", lambda pw: (_ for _ in ()).throw(Exception("fail")))
    monkeypatch.setattr(
        menu.db_introspect,
        "parse_wp_config",
        lambda path: db_introspect.WPConfig("wpdb", None, None, None),
    )
    warns = []
    monkeypatch.setattr(menu, "_warn", lambda msg: warns.append(msg))

    def fake_secret(message):
        class R:
            def execute(self):
                return ""

        return R()

    menu.inquirer = SimpleNamespace(secret=fake_secret, text=lambda **k: None)

    result = menu._db_picker_with_fallbacks("/a")
    assert result == "wpdb"
    assert warns == ["Could not list databases. Using DB from wp-config.php: wpdb"]

