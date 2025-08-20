import logging
from typing import List
from types import SimpleNamespace

import logging
from typing import List

import pytest

from lampkitctl import menu


def test_run_menu_routing(monkeypatch):
    """Ensure menu invokes installation with selected options."""

    sequence = iter(["Install LAMP server", "Auto"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: True)

    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)

    called = {}

    def fake_install_lamp(db_engine: str, wait_apt_lock: int, dry_run: bool, **kwargs):
        called["engine"] = db_engine
        called["wait"] = wait_apt_lock
        return "mysql"

    monkeypatch.setattr(menu, "install_lamp", fake_install_lamp)
    monkeypatch.setattr(menu, "ensure_db_root_password", lambda: "pw")
    monkeypatch.setattr(
        menu.db_ops, "set_root_password", lambda eng, pw, plugin, dry_run: called.update({"pwd": pw})
    )

    menu.run_menu(dry_run=True)
    assert called["engine"] == "auto"
    assert called["wait"] == 120
    assert called["pwd"] == "pw"


def test_validate_domain_invalid():
    """Domain validation should reject malformed names."""
    with pytest.raises(ValueError):
        menu.validate_domain("bad_domain")


def test_create_site_propagates_and_masks(monkeypatch, caplog):
    """create_site should pass dry_run and mask sensitive info."""
    caplog.set_level(logging.INFO)
    calls: List[tuple] = []

    monkeypatch.setattr(menu.system_ops, "create_web_directory", lambda *a, **k: calls.append(("cwd", k["dry_run"])))
    monkeypatch.setattr(menu.system_ops, "create_virtualhost", lambda *a, **k: calls.append(("vh", k["dry_run"])))
    monkeypatch.setattr(menu.system_ops, "enable_site", lambda *a, **k: calls.append(("en", k["dry_run"])))
    monkeypatch.setattr(menu.system_ops, "add_host_entry", lambda *a, **k: calls.append(("host", k["dry_run"])))
    monkeypatch.setattr(menu.db_ops, "create_database_and_user", lambda *a, **k: calls.append(("db", k["dry_run"])))
    monkeypatch.setattr(menu.wp_ops, "install_wordpress", lambda *a, **k: calls.append(("wp", k["dry_run"])))

    menu.create_site(
        domain="example.com",
        doc_root="/var/www/example.com",
        db_name="db",
        db_user="user",
        db_password="secret",
        wordpress=True,
        dry_run=True,
    )

    assert all(dry for _, dry in calls)
    assert "secret" not in caplog.text


def test_list_sites_empty(monkeypatch, capsys):
    monkeypatch.setattr(menu, "list_installed_sites", lambda: [])
    menu._list_sites_flow()
    out = capsys.readouterr().out
    assert "No sites found" in out
