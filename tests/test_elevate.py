"""Tests for elevation helpers."""
from __future__ import annotations

import sys

import pytest

from lampkitctl import elevate, utils


def test_build_sudo_cmd_prefixes(monkeypatch) -> None:
    """build_sudo_cmd should prefix the provided argv with sudo."""

    cmd = elevate.build_sudo_cmd(["/venv/bin/lampkitctl", "install-lamp", "--x"])
    assert cmd == ["sudo", "/venv/bin/lampkitctl", "install-lamp", "--x"]


def test_build_sudo_cmd_plain(monkeypatch) -> None:
    """build_sudo_cmd leaves the argv untouched apart from sudo."""

    cmd = elevate.build_sudo_cmd(["lampkitctl", "install-lamp"])
    assert cmd == ["sudo", "lampkitctl", "install-lamp"]


def test_maybe_reexec_execs(monkeypatch) -> None:
    """When not root and interactive, the process should exec sudo."""

    monkeypatch.setattr(elevate.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(elevate, "resolve_self_executable", lambda: "/venv/bin/lampkitctl")
    monkeypatch.setattr(utils, "prompt_yes_no", lambda *a, **k: True)
    monkeypatch.setattr(utils, "is_non_interactive", lambda: False)
    called = {}
    monkeypatch.setattr(elevate.os, "execvp", lambda *a: called.setdefault("cmd", list(a)))
    elevate.maybe_reexec_with_sudo(["lampkitctl", "install-lamp"], non_interactive=False, dry_run=False)
    assert called["cmd"] == ["sudo", ["sudo", "/venv/bin/lampkitctl", "install-lamp"]]


def test_maybe_reexec_non_interactive(monkeypatch, capsys) -> None:
    """Non-interactive runs should exit with guidance."""

    monkeypatch.setattr(elevate.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(utils, "is_non_interactive", lambda: False)
    monkeypatch.setattr(utils, "echo_err", lambda msg: print(msg, file=sys.stderr))
    with pytest.raises(SystemExit) as exc:
        elevate.maybe_reexec_with_sudo(["lampkitctl"], non_interactive=True, dry_run=False)
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "sudo $(command -v lampkitctl)" in err


def test_maybe_reexec_dry_run(monkeypatch) -> None:
    """Dry-run should bypass elevation logic."""

    monkeypatch.setattr(elevate.os, "geteuid", lambda: 1000)
    called = {}
    monkeypatch.setattr(elevate.os, "execvp", lambda *a: called.setdefault("cmd", list(a)))
    elevate.maybe_reexec_with_sudo(["lampkitctl"], non_interactive=False, dry_run=True)
    assert called == {}
