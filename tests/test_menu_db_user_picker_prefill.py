from types import SimpleNamespace
from lampkitctl import menu, db_introspect


def test_db_user_picker_prefills_from_wp_config(monkeypatch) -> None:
    monkeypatch.setattr(
        menu.dbi,
        "list_users",
        lambda password=None: (_ for _ in ()).throw(Exception("fail")),
    )
    monkeypatch.setattr(
        menu.dbi,
        "list_users_with_sudo",
        lambda pw: (_ for _ in ()).throw(Exception("fail")),
    )
    monkeypatch.setattr(
        menu.db_introspect,
        "parse_wp_config",
        lambda path: db_introspect.WPConfig(None, "wpuser", "dbhost", None),
    )

    warns: list[str] = []
    monkeypatch.setattr(menu, "_warn", lambda msg: warns.append(msg))

    def fake_secret(message):
        class R:
            def execute(self):
                return ""

        return R()

    menu.inquirer = SimpleNamespace(secret=fake_secret, text=lambda **k: None)

    result = menu._db_user_picker_with_fallbacks("/a")
    assert result == "wpuser@dbhost"
    assert warns == [
        "Could not list DB users. Using wp-config.php user: wpuser@dbhost"
    ]

