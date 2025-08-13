"""Interactive text-based menu for lampkitctl."""
from __future__ import annotations

import getpass
import logging
import re
import sys
from typing import Iterable, List, Optional

from . import db_ops, preflight, system_ops, utils, wp_ops
from .elevate import maybe_reexec_with_sudo

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from InquirerPy import inquirer
except Exception:  # pragma: no cover - handled gracefully
    inquirer = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_domain(domain: str) -> str:
    """Validate a domain name.

    Args:
        domain: Domain string to validate.

    Returns:
        The original domain if valid.

    Raises:
        ValueError: If the domain does not match the expected format.
    """
    pattern = re.compile(
        r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.[A-Za-z]{2,63}$"
    )
    if not pattern.match(domain):
        raise ValueError("Invalid domain name")
    return domain


def validate_db_identifier(name: str) -> str:
    """Validate MySQL identifier (database or user name).

    Args:
        name: Identifier to validate.

    Returns:
        The original name if valid.

    Raises:
        ValueError: If ``name`` contains invalid characters.
    """
    if not re.match(r"^[A-Za-z0-9_]+$", name):
        raise ValueError("Invalid database identifier")
    return name


# ---------------------------------------------------------------------------
# Core actions (testable)
# ---------------------------------------------------------------------------

def install_lamp(db_engine: str = "auto", dry_run: bool = False) -> None:
    """Install required LAMP components."""

    maybe_reexec_with_sudo(sys.argv, non_interactive=False, dry_run=dry_run)
    checks = preflight.checks_for("install-lamp")
    try:
        preflight.ensure_or_fail(checks, dry_run=dry_run)
    except SystemExit:
        return
    system_ops.install_lamp_stack(
        None if db_engine == "auto" else db_engine, dry_run=dry_run
    )


def create_site(
    domain: str,
    doc_root: str,
    db_name: str,
    db_user: str,
    db_password: str,
    wordpress: bool,
    dry_run: bool = False,
) -> None:
    """Create a site with Apache, MySQL and optional WordPress.

    Args:
        domain: Domain for the new site.
        doc_root: Document root directory.
        db_name: Name of the MySQL database.
        db_user: MySQL username.
        db_password: MySQL password (masked in logs).
        wordpress: If ``True`` install WordPress.
        dry_run: Log actions without executing.
    """
    maybe_reexec_with_sudo(sys.argv, non_interactive=False, dry_run=dry_run)
    logger.info(
        "create_site",
        extra={
            "domain": domain,
            "doc_root": doc_root,
            "db_name": db_name,
            "db_user": db_user,
            "wordpress": wordpress,
            "dry_run": dry_run,
        },
    )
    system_ops.create_web_directory(doc_root, dry_run=dry_run)
    system_ops.create_virtualhost(domain, doc_root, dry_run=dry_run)
    system_ops.enable_site(domain, dry_run=dry_run)
    system_ops.add_host_entry(domain, dry_run=dry_run)
    db_ops.create_database_and_user(db_name, db_user, db_password, dry_run=dry_run)
    if wordpress:
        wp_ops.install_wordpress(doc_root, db_name, db_user, db_password, dry_run=dry_run)


def uninstall_site(
    domain: str,
    doc_root: str,
    db_name: str,
    db_user: str,
    remove_db: bool,
    dry_run: bool = False,
) -> None:
    """Remove an existing site.

    Args:
        domain: Domain of the site to remove.
        doc_root: Document root path.
        db_name: Database name.
        db_user: Database user.
        remove_db: If ``True`` drop database and user.
        dry_run: Log actions without executing.
    """
    maybe_reexec_with_sudo(sys.argv, non_interactive=False, dry_run=dry_run)
    logger.info("uninstall_site", extra={"domain": domain, "dry_run": dry_run})
    system_ops.remove_virtualhost(domain, dry_run=dry_run)
    system_ops.remove_host_entry(domain, dry_run=dry_run)
    system_ops.remove_web_directory(doc_root, dry_run=dry_run)
    if remove_db:
        db_ops.drop_database_and_user(db_name, db_user, dry_run=dry_run)


def set_wp_permissions(doc_root: str, dry_run: bool = False) -> None:
    """Set secure permissions for a WordPress installation.

    Args:
        doc_root: Path to the WordPress installation.
        dry_run: Log actions without executing.
    """
    maybe_reexec_with_sudo(sys.argv, non_interactive=False, dry_run=dry_run)
    logger.info("set_wp_permissions", extra={"doc_root": doc_root, "dry_run": dry_run})
    wp_ops.set_permissions(doc_root, dry_run=dry_run)


def generate_ssl(domain: str, dry_run: bool = False) -> None:
    """Generate an SSL certificate using certbot.

    Args:
        domain: Domain for the certificate.
        dry_run: Log actions without executing.
    """
    maybe_reexec_with_sudo(sys.argv, non_interactive=False, dry_run=dry_run)
    logger.info("generate_ssl", extra={"domain": domain, "dry_run": dry_run})
    utils.run_command(["certbot", "--apache", "-d", domain], dry_run)


def list_installed_sites() -> List[dict]:
    """Return installed sites from Apache configuration."""
    return system_ops.list_sites()


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _select(message: str, choices: Iterable[str]) -> str:
    if inquirer:  # pragma: no cover - optional path
        return inquirer.select(message=message, choices=list(choices)).execute()
    while True:
        print(message)
        choices_list = list(choices)
        for idx, choice in enumerate(choices_list, 1):
            print(f"{idx}) {choice}")
        resp = input("Select: ").strip()
        if resp.isdigit() and 1 <= int(resp) <= len(choices_list):
            return choices_list[int(resp) - 1]


def _text(message: str, default: Optional[str] = None) -> str:
    if inquirer:  # pragma: no cover
        return inquirer.text(message=message, default=default).execute()
    prompt = f"{message}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    resp = input(prompt).strip()
    return resp or (default or "")


def _password(message: str) -> str:
    if inquirer:  # pragma: no cover
        return inquirer.secret(message=message).execute()
    return getpass.getpass(message + ": ")


def _confirm(message: str, default: bool = False) -> bool:
    if inquirer:  # pragma: no cover
        return inquirer.confirm(message=message, default=default).execute()
    return utils.prompt_confirm(message, default=default)


# ---------------------------------------------------------------------------
# Interactive flows
# ---------------------------------------------------------------------------

def _create_site_flow(dry_run: bool) -> None:
    domain = _text("Main > Create a site > Domain")
    if not domain:
        return
    try:
        validate_domain(domain)
    except ValueError as exc:  # pragma: no cover - simple validation path
        print(exc)
        return
    doc_root_default = f"/var/www/{domain}"
    doc_root = _text("Main > Create a site > Document root", default=doc_root_default)
    db_name = _text("Main > Create a site > Database name")
    try:
        validate_db_identifier(db_name)
    except ValueError as exc:  # pragma: no cover
        print(exc)
        return
    db_user = _text("Main > Create a site > Database user")
    try:
        validate_db_identifier(db_user)
    except ValueError as exc:  # pragma: no cover
        print(exc)
        return
    db_password = _password("Main > Create a site > Database password")
    wordpress = _confirm("Main > Create a site > Install WordPress?", default=False)
    create_site(domain, doc_root, db_name, db_user, db_password, wordpress, dry_run=dry_run)


def _uninstall_site_flow(dry_run: bool) -> None:
    sites = list_installed_sites()
    if not sites:
        print("No sites found")
        return
    choices = [s["domain"] for s in sites]
    domain = _select("Main > Uninstall site > Select domain", choices)
    doc_root = next(s["doc_root"] for s in sites if s["domain"] == domain)
    db_name = _text("Main > Uninstall site > Database name")
    db_user = _text("Main > Uninstall site > Database user")
    if not _confirm(f"Remove site {domain}?", default=False):
        return
    if not _confirm("This action is destructive. Continue?", default=False):
        return
    remove_db = _confirm("Drop database and user?", default=False)
    uninstall_site(domain, doc_root, db_name, db_user, remove_db, dry_run=dry_run)


def _wp_permissions_flow(dry_run: bool) -> None:
    doc_root = _text("Main > Set WordPress permissions > Path")
    if not doc_root:
        return
    try:
        preflight.ensure_or_fail(
            preflight.checks_for("wp-permissions", doc_root=doc_root)
        )
    except SystemExit:
        return
    set_wp_permissions(doc_root, dry_run=dry_run)


def _generate_ssl_flow(dry_run: bool) -> None:
    sites = list_installed_sites()
    if not sites:
        print("No domains available")
        return
    choices = [s["domain"] for s in sites]
    domain = _select("Main > Generate SSL certificate > Select domain", choices)
    try:
        preflight.ensure_or_fail(
            preflight.checks_for("generate-ssl", domain=domain)
        )
    except SystemExit:
        if _confirm("Run install-lamp now?", default=False):
            install_lamp(dry_run=dry_run)
        return
    generate_ssl(domain, dry_run=dry_run)


def _list_sites_flow() -> None:
    sites = list_installed_sites()
    for site in sites:
        print(f"{site['domain']} -> {site['doc_root']}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_menu(dry_run: bool = False) -> None:
    """Run the interactive menu.

    Args:
        dry_run: When ``True`` log actions without executing commands.
    """
    options = [
        "Install LAMP server",
        "Create a site",
        "Uninstall site",
        "Set WordPress permissions",
        "Generate SSL certificate",
        "List installed sites",
        "Exit",
    ]
    while True:
        choice = _select("Main > Choose an option", options)
        if choice == "Install LAMP server":
            engine_choice = _select(
                "Main > Install LAMP server > Database engine",
                ["Auto", "MySQL", "MariaDB"],
            )
            install_lamp(
                db_engine=engine_choice.lower() if engine_choice != "Auto" else "auto",
                dry_run=dry_run,
            )
        elif choice == "Create a site":
            try:
                preflight.ensure_or_fail(
                    preflight.checks_for("create-site")
                )
            except SystemExit:
                if _confirm("Run install-lamp now?", default=False):
                    install_lamp(dry_run=dry_run)
                continue
            _create_site_flow(dry_run=dry_run)
        elif choice == "Uninstall site":
            try:
                preflight.ensure_or_fail(
                    preflight.checks_for("uninstall-site")
                )
            except SystemExit:
                if _confirm("Run install-lamp now?", default=False):
                    install_lamp(dry_run=dry_run)
                continue
            _uninstall_site_flow(dry_run=dry_run)
        elif choice == "Set WordPress permissions":
            _wp_permissions_flow(dry_run=dry_run)
        elif choice == "Generate SSL certificate":
            _generate_ssl_flow(dry_run=dry_run)
        elif choice == "List installed sites":
            if not preflight.has_cmd("apache2").ok or not preflight.apache_paths_present().ok:
                print("Apache not installed. No sites to list.")
            else:
                _list_sites_flow()
        elif choice == "Exit":
            break
