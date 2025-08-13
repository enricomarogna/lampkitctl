"""Preflight checks and utilities for lampkitctl."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable, List, Optional

import click

from . import utils

# ---------------------------------------------------------------------------
# Basic check helpers
# ---------------------------------------------------------------------------

def is_root_or_sudo() -> bool:
    """Return ``True`` when running as root or via sudo."""
    return os.geteuid() == 0 or "SUDO_UID" in os.environ


def is_supported_os() -> bool:
    """Check whether the host is a supported Ubuntu release."""
    try:
        content = Path("/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        return False
    id_match = re.search(r"^ID=(.*)$", content, re.MULTILINE)
    ver_match = re.search(r"^VERSION_ID=\"?(.*?)\"?$", content, re.MULTILINE)
    if not id_match or not ver_match:
        return False
    distro = id_match.group(1)
    version = ver_match.group(1)
    return distro == "ubuntu" and version in {"20.04", "22.04", "24.04"}


def has_cmd(name: str) -> bool:
    """Return ``True`` if ``name`` is available on ``PATH``."""
    return shutil.which(name) is not None


def service_installed(name: str) -> bool:
    """Alias for :func:`has_cmd` for semantic clarity."""
    return has_cmd(name)


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


def apache_paths_present() -> bool:
    """Check that Apache configuration directories exist."""
    return Path("/etc/apache2").exists() and Path("/etc/apache2/sites-available").exists()


def can_write(path: str) -> bool:
    """Return ``True`` if the current user can write to ``path``."""
    return os.access(path, os.W_OK)


def is_wordpress_dir(path: str | Path) -> bool:
    """Determine whether ``path`` appears to be a WordPress installation."""
    p = Path(path)
    return (
        (p / "wp-config.php").exists()
        and (p / "wp-content").exists()
        and (p / "wp-includes").exists()
    )

# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

Check = Callable[[], Optional[str]]


def collect_errors(checks: Iterable[Check]) -> List[str]:
    """Execute ``checks`` and return a list of error messages."""
    errors: List[str] = []
    for check in checks:
        msg = check()
        if msg:
            errors.append(msg)
    return errors


def ensure_or_fail(
    checks: Iterable[Check],
    command: str,
    *,
    exit_code: int = 2,
    interactive: bool = True,
) -> None:
    """Validate ``checks`` and abort if any fail."""
    errors = collect_errors(checks)
    if not errors:
        return
    click.echo(f"Preflight failed: {command}")
    for err in errors:
        click.echo(f"- {err}")
    if interactive and utils.prompt_confirm("Continue anyway?", default=False):
        return
    raise SystemExit(exit_code)

# ---------------------------------------------------------------------------
# Check factories
# ---------------------------------------------------------------------------


def checks_for(command: str, **kwargs) -> List[Check]:
    """Return the appropriate preflight checks for ``command``."""
    domain = kwargs.get("domain", "")
    doc_root = kwargs.get("doc_root", "")

    if command == "install-lamp":
        return [
            lambda: None
            if is_root_or_sudo()
            else "Root privileges required. Run with sudo.",
            lambda: None if has_cmd("apt") else "apt not found. Install apt package manager.",
            lambda: None if has_cmd("systemctl") else "systemctl not found. Install systemd.",
            lambda: None
            if is_supported_os()
            else "Unsupported OS. Supported: Ubuntu 20.04/22.04/24.04.",
        ]
    if command == "create-site":
        return [
            lambda: None if has_cmd("apache2") else "Apache not installed. Run: install-lamp.",
            lambda: None if apache_paths_present() else "Apache paths missing. Run: install-lamp.",
            lambda: None if has_cmd("mysql") else "MySQL not installed. Run: install-lamp.",
            lambda: None if has_cmd("php") else "PHP not installed. Run: install-lamp.",
            lambda: None if can_write("/etc/hosts") else "Cannot write /etc/hosts. Run as root.",
            lambda: None if can_write("/var/www") else "Cannot write /var/www. Check permissions.",
        ]
    if command == "uninstall-site":
        return [
            lambda: None if has_cmd("apache2") else "Apache not installed. Run: install-lamp.",
            lambda: None if apache_paths_present() else "Apache paths missing. Run: install-lamp.",
            lambda: None if has_cmd("mysql") else "MySQL not installed. Run: install-lamp.",
            lambda: None if can_write("/etc/hosts") else "Cannot write /etc/hosts. Run as root.",
            lambda: None if can_write("/var/www") else "Cannot write /var/www. Check permissions.",
        ]
    if command == "wp-permissions":
        return [
            lambda: None if has_cmd("apache2") else "Apache not installed. Run: install-lamp.",
            lambda: None if apache_paths_present() else "Apache paths missing. Run: install-lamp.",
            lambda: None if Path(doc_root).exists() else f"{doc_root} does not exist.",
            lambda: None
            if is_wordpress_dir(doc_root)
            else f"{doc_root} is not a WordPress directory.",
        ]
    if command == "generate-ssl":
        vhost_available = Path(f"/etc/apache2/sites-available/{domain}.conf").exists()
        vhost_enabled = Path(f"/etc/apache2/sites-enabled/{domain}.conf").exists()
        return [
            lambda: None if has_cmd("apache2") else "Apache not installed. Run: install-lamp.",
            lambda: None if apache_paths_present() else "Apache paths missing. Run: install-lamp.",
            lambda: None if vhost_available else f"Virtual host {domain} missing. Create the site first.",
            lambda: None
            if vhost_enabled
            else f"Virtual host {domain} not enabled. Run: a2ensite {domain} && systemctl reload apache2.",
            lambda: None
            if has_cmd("certbot")
            else "certbot not installed. Run: apt install certbot python3-certbot-apache.",
        ]
    return []
