"""Preflight checks and utilities for lampkitctl."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterable, List

import click

from . import utils


class Severity(Enum):
    """Severity levels for preflight checks."""

    WARNING = auto()
    BLOCKING = auto()


@dataclass
class CheckResult:
    """Result of a single preflight check."""

    ok: bool
    message: str
    severity: Severity = Severity.BLOCKING


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

def is_root_or_sudo() -> CheckResult:
    """Ensure the current user has root privileges."""

    ok = os.geteuid() == 0 or "SUDO_UID" in os.environ
    return CheckResult(ok, "Root privileges required. Run with sudo.")


def is_supported_os() -> CheckResult:
    """Verify the host is a supported Ubuntu release."""

    try:
        content = Path("/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        content = ""
    id_match = re.search(r"^ID=(.*)$", content, re.MULTILINE)
    ver_match = re.search(r"^VERSION_ID=\"?(.*?)\"?$", content, re.MULTILINE)
    ok = bool(
        id_match
        and ver_match
        and id_match.group(1) == "ubuntu"
        and ver_match.group(1) in {"20.04", "22.04", "24.04"}
    )
    return CheckResult(
        ok, "Unsupported OS. Supported: Ubuntu 20.04/22.04/24.04."
    )


def has_cmd(
    name: str, msg: str | None = None, severity: Severity = Severity.BLOCKING
) -> CheckResult:
    """Return a :class:`CheckResult` verifying ``name`` exists on ``PATH``."""

    ok = shutil.which(name) is not None
    return CheckResult(ok, msg or f"{name} not found. Install {name}.", severity)


def apache_paths_present() -> CheckResult:
    """Check for Apache configuration directories."""

    ok = Path("/etc/apache2").exists() and Path("/etc/apache2/sites-available").exists()
    return CheckResult(ok, "Apache paths missing. Run: install-lamp.")


def can_write(path: str) -> CheckResult:
    """Ensure the current user can write to ``path``."""

    ok = os.access(path, os.W_OK)
    return CheckResult(ok, f"Cannot write {path}. Check permissions.")


def path_exists(path: str | Path) -> CheckResult:
    """Return ``CheckResult`` indicating whether ``path`` exists."""

    p = Path(path)
    return CheckResult(p.exists(), f"{path} does not exist.")


def is_wordpress_dir(path: str | Path) -> CheckResult:
    """Check whether ``path`` looks like a WordPress installation."""

    p = Path(path)
    ok = (
        (p / "wp-config.php").exists()
        and (p / "wp-content").exists()
        and (p / "wp-includes").exists()
    )
    return CheckResult(ok, f"{path} is not a WordPress directory.")


def service_running(name: str) -> bool:
    """Return ``True`` if ``systemctl`` reports ``name`` active."""

    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def summarize(results: List[CheckResult]) -> str:
    """Return a human readable summary for failing ``results``."""

    lines = ["Preflight failed:"]
    for r in results:
        lines.append(f"- {r.message}")
    return "\n".join(lines)


def ensure_or_fail(
    results: Iterable[CheckResult],
    *,
    allow_warnings_continue: bool = True,
    interactive: bool = True,
    dry_run: bool = False,
) -> None:
    """Evaluate ``results`` and abort on failure.

    ``SystemExit(2)`` is raised on BLOCKING failures unless ``dry_run`` is ``True``.
    WARNING failures may prompt for confirmation when ``interactive``.
    """

    blocking = [r for r in results if (not r.ok and r.severity is Severity.BLOCKING)]
    warnings = [r for r in results if (not r.ok and r.severity is Severity.WARNING)]

    if blocking:
        click.echo(summarize(blocking), err=True)
        if not dry_run:
            raise SystemExit(2)
    if warnings:
        click.echo(summarize(warnings), err=True)
        if not allow_warnings_continue or not interactive:
            raise SystemExit(2)
        proceed = utils.prompt_confirm(
            "Some prerequisites are missing. Continue anyway?", default=False
        )
        if not proceed:
            raise SystemExit(2)


# ---------------------------------------------------------------------------
# Check factories
# ---------------------------------------------------------------------------

def checks_for(command: str, **kwargs) -> List[CheckResult]:
    """Return the appropriate preflight checks for ``command``."""

    domain = kwargs.get("domain", "")
    doc_root = kwargs.get("doc_root", "")

    if command == "install-lamp":
        return [
            is_root_or_sudo(),
            has_cmd("apt", "apt not found. Install apt package manager."),
            has_cmd("systemctl", "systemctl not found. Install systemd."),
            is_supported_os(),
        ]
    if command == "create-site":
        return [
            has_cmd("apache2", "Apache not installed. Run: install-lamp."),
            apache_paths_present(),
            has_cmd("mysql", "MySQL not installed. Run: install-lamp."),
            has_cmd("php", "PHP not installed. Run: install-lamp."),
            can_write("/etc/hosts"),
            can_write("/var/www"),
        ]
    if command == "uninstall-site":
        return [
            has_cmd("apache2", "Apache not installed. Run: install-lamp."),
            apache_paths_present(),
            has_cmd("mysql", "MySQL not installed. Run: install-lamp."),
            can_write("/etc/hosts"),
            can_write("/var/www"),
        ]
    if command == "wp-permissions":
        return [
            has_cmd("apache2", "Apache not installed. Run: install-lamp."),
            apache_paths_present(),
            path_exists(doc_root),
            is_wordpress_dir(doc_root),
        ]
    if command == "generate-ssl":
        vhost_available = Path(
            f"/etc/apache2/sites-available/{domain}.conf"
        ).exists()
        vhost_enabled = Path(
            f"/etc/apache2/sites-enabled/{domain}.conf"
        ).exists()
        return [
            has_cmd("apache2", "Apache not installed. Run: install-lamp."),
            apache_paths_present(),
            CheckResult(
                vhost_available,
                f"Virtual host {domain} missing. Create the site first.",
            ),
            CheckResult(
                vhost_enabled,
                f"Virtual host {domain} not enabled. Run: a2ensite {domain} && systemctl reload apache2.",
            ),
            has_cmd(
                "certbot",
                "certbot not installed. Run: apt install certbot python3-certbot-apache.",
            ),
        ]
    return []

