import logging
from typing import List

import logging
from typing import List

import pytest

from lampkitctl import menu


def test_run_menu_routing(monkeypatch):
    """Ensure menu builds the correct CLI invocation."""
    sequence = iter(["Install LAMP server", "Auto", "Exit"])
    monkeypatch.setattr(menu, "_select", lambda msg, choices: next(sequence))
    monkeypatch.setattr(menu, "_confirm", lambda msg, default=True: True)

    monkeypatch.setattr(menu.preflight, "ensure_or_fail", lambda *a, **k: None)
    monkeypatch.setattr(menu, "resolve_self_executable", lambda: "/venv/lampkitctl")

    called = {}

    def fake_call(args):
        called["args"] = args
        return 0

    monkeypatch.setattr(menu.subprocess, "call", fake_call)

    menu.run_menu(dry_run=True)
    assert called["args"] == [
        "/venv/lampkitctl",
        "install-lamp",
        "--db-engine",
        "auto",
        "--wait-apt-lock",
        "120",
        "--set-db-root-pass",
    ]


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
