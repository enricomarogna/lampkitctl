"""Interactive text-based menu for lampkitctl."""
from __future__ import annotations

import getpass
import logging
import os
import re
import subprocess
import sys
from typing import Iterable, List, Optional

from . import (
    apache_vhosts,
    db_ops,
    preflight,
    preflight_locks,
    system_ops,
    utils,
    wp_ops,
    db_introspect,
)
from .utils import echo_error, echo_warn, echo_ok, echo_info, echo_title
from .elevate import (
    build_sudo_cmd,
    maybe_reexec_with_sudo,
    resolve_self_executable,
)

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from InquirerPy import inquirer
except Exception:  # pragma: no cover - handled gracefully
    inquirer = None


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

def _run_cli(args: list[str], *, dry_run: bool = False) -> int:
    exe = resolve_self_executable()
    if exe:
        base = [exe]
    else:
        base = [sys.executable, "-m", "lampkitctl"]
    cmd = base + args
    if os.geteuid() != 0 and not dry_run:
        cmd = build_sudo_cmd(cmd)
    return subprocess.call(cmd)


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


def _list_dbs_interactive() -> list[str] | None:
    """List databases, prompting for root password if required."""
    try:
        return db_introspect.list_databases().databases
    except Exception:
        pass

    if inquirer:  # pragma: no cover - optional dependency
        pwd = inquirer.secret(message="Database root password:").execute()
    else:  # pragma: no cover - no InquirerPy
        pwd = getpass.getpass("Database root password: ")
    if not pwd:
        return None
    db_introspect.cache_root_password(pwd)

    try:
        return db_introspect.list_databases(password=pwd).databases
    except Exception:
        try:
            return db_introspect.list_databases().databases
        except Exception:
            echo_error(
                "Failed to list databases even after providing password.\nFalling back to manual database entry"
            )
            return None


# ---------------------------------------------------------------------------
# Core actions (testable)
# ---------------------------------------------------------------------------

def install_lamp(
    db_engine: str = "auto",
    wait_apt_lock: int = 120,
    dry_run: bool = False,
) -> None:
    """Install required LAMP components."""

    maybe_reexec_with_sudo(sys.argv, non_interactive=False, dry_run=dry_run)
    if wait_apt_lock > 0:
        info = preflight_locks.wait_for_lock(wait_apt_lock)
        if info.locked:
            return
    else:
        if preflight_locks.detect_lock().locked:
            return
    checks = preflight.checks_for("install-lamp")
    try:
        preflight.ensure_or_fail(checks, dry_run=dry_run)
    except SystemExit:
        return
    system_ops.install_lamp_stack(
        None if db_engine == "auto" else db_engine,
        dry_run=dry_run,
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
    return [
        {"domain": v.domain, "doc_root": v.docroot or ""}
        for v in apache_vhosts.list_vhosts()
    ]


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


def _text(message: str, default: str = "") -> str:
    if inquirer:  # pragma: no cover
        return inquirer.text(message=message, default=default).execute()
    prompt = f"{message}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    resp = input(prompt).strip()
    return resp or default


def _password(message: str) -> str:
    if inquirer:  # pragma: no cover
        return inquirer.secret(message=message).execute()
    return getpass.getpass(message + ": ")


def _confirm(message: str, default: bool = False) -> bool:
    if inquirer:  # pragma: no cover
        return inquirer.confirm(message=message, default=default).execute()
    return utils.prompt_confirm(message, default=default)


def _choose_site() -> apache_vhosts.VHost | str | None:
    sites = apache_vhosts.list_vhosts()
    if not sites:
        echo_error("No sites found")
        return None
    choices = [
        {
            "name": f"{v.domain}  —  {v.docroot or '(no DocumentRoot)'}" + ("  [SSL]" if v.ssl else ""),
            "value": v,
        }
        for v in sites
    ]
    choices.append({"name": "Custom...", "value": "custom"})
    if inquirer:  # pragma: no cover
        return inquirer.select(
            message="Select a site",
            choices=choices,
            default=choices[0]["value"],
        ).execute()
    while True:
        print("Select a site")
        for idx, choice in enumerate(choices, 1):
            print(f"{idx}) {choice['name']}")
        resp = input("Select: ").strip()
        if resp.isdigit() and 1 <= int(resp) <= len(choices):
            return choices[int(resp) - 1]["value"]


def _choose_database(doc_root: str | None) -> str:
    dblist = _list_dbs_interactive()
    if dblist is None:
        echo_warn("Falling back to manual database entry")
        return _text("Main > Uninstall site > Database name")
    preselect = None
    if doc_root:
        cfg = db_introspect.parse_wp_config(doc_root)
        if cfg and cfg.name:
            if cfg.name in dblist:
                preselect = cfg.name
            else:
                echo_warn(f"DB from wp-config.php not found on server: {cfg.name}")
    choices = [{"name": db, "value": db} for db in dblist]
    if preselect and preselect in dblist:
        default_value = preselect
    else:
        default_value = dblist[0] if dblist else None
    choices.append({"name": "Custom...", "value": "__CUSTOM__"})
    if inquirer and dblist:  # pragma: no cover - optional path
        selected = inquirer.select(
            message="Select database",
            choices=choices,
            default=default_value,
        ).execute()
    else:
        if not dblist:
            return _text("Main > Uninstall site > Database name")
        while True:
            print("Select database")
            for idx, choice in enumerate(choices, 1):
                print(f"{idx}) {choice['name']}")
            resp = input("Select: ").strip()
            if resp.isdigit() and 1 <= int(resp) <= len(choices):
                selected = choices[int(resp) - 1]["value"]
                break
    if selected == "__CUSTOM__":
        if inquirer:  # pragma: no cover
            selected = inquirer.text(message="Enter database name:").execute()
        else:
            selected = _text("Enter database name:")
    return selected


# ---------------------------------------------------------------------------
# Interactive flows
# ---------------------------------------------------------------------------

def _create_site_flow(dry_run: bool) -> None:
    checks = [
        preflight.is_apache_installed(),
        preflight.apache_paths_present(),
        preflight.is_mysql_installed(),
        preflight.is_php_installed(),
    ]
    missing = [c for c in checks if not c.ok]
    if missing:
        echo_error(
            "LAMP stack not installed/configured. You must run install-lamp before creating a site."
        )
        if _confirm("Run install-lamp now?"):
            rc = _run_cli(["install-lamp"], dry_run=dry_run)
            if rc != 0:
                echo_error("install-lamp failed. Please fix errors and retry.")
                return
        else:
            return
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
    args = [
        "create-site",
        domain,
        "--doc-root",
        doc_root,
        "--db-name",
        db_name,
        "--db-user",
        db_user,
        "--db-password",
        db_password,
    ]
    if wordpress:
        args.append("--wordpress")
    rc = _run_cli(args, dry_run=dry_run)
    if rc != 0 and _confirm("Run install-lamp now?", default=True):
        if _run_cli(["install-lamp"], dry_run=dry_run) == 0:
            _run_cli(args, dry_run=dry_run)


def _uninstall_site_flow(dry_run: bool) -> None:
    vhost = _choose_site()
    if not vhost:
        return
    if vhost == "custom":
        domain = _text("Main > Uninstall site > Domain")
        if not domain:
            return
        doc_root = _text("Main > Uninstall site > Document root", default="")
    else:
        domain = vhost.domain
        doc_root = vhost.docroot or ""
    db_name = _choose_database(doc_root)
    db_user = _text("Main > Uninstall site > Database user")
    if not _confirm(f"Remove site {domain}?", default=False):
        return
    if not _confirm("This action is destructive. Continue?", default=False):
        return
    args = [
        "uninstall-site",
        domain,
        "--doc-root",
        doc_root,
        "--db-name",
        db_name,
        "--db-user",
        db_user,
    ]
    rc = _run_cli(args, dry_run=dry_run)
    if rc != 0 and _confirm("Run install-lamp now?", default=True):
        if _run_cli(["install-lamp"], dry_run=dry_run) == 0:
            _run_cli(args, dry_run=dry_run)


def _wp_permissions_flow(dry_run: bool) -> None:
    checks = [
        preflight.is_apache_installed(),
        preflight.apache_paths_present(),
    ]
    missing = [c for c in checks if not c.ok]
    if missing:
        echo_error(
            "LAMP stack not installed/configured. You must run install-lamp before setting permissions."
        )
        if _confirm("Run install-lamp now?"):
            rc = _run_cli(["install-lamp"], dry_run=dry_run)
            if rc != 0:
                echo_error("install-lamp failed. Please fix errors and retry.")
            else:
                _wp_permissions_flow(dry_run=dry_run)
        return
    vhost = _choose_site()
    if not vhost:
        return
    if vhost == "custom":
        doc_root = _text("Main > Set WordPress permissions > Path", default="")
        if not doc_root:
            return
        while True:
            checks = [
                preflight.path_exists(doc_root),
                preflight.is_wordpress_dir(doc_root),
            ]
            if all(c.ok for c in checks):
                break
            echo_error(preflight.summarize([c for c in checks if not c.ok]))
            doc_root = _text("Main > Set WordPress permissions > Path", default="")
            if not doc_root:
                return
    else:
        doc_root = vhost.docroot
        if not doc_root:
            echo_error("Selected vhost has no DocumentRoot")
            return
        checks = [
            preflight.path_exists(doc_root),
            preflight.is_wordpress_dir(doc_root),
        ]
        if not all(c.ok for c in checks):
            echo_error(preflight.summarize([c for c in checks if not c.ok]))
            return
    rc = _run_cli(["wp-permissions", doc_root], dry_run=dry_run)
    if rc != 0 and _confirm("Run install-lamp now?", default=True):
        if _run_cli(["install-lamp"], dry_run=dry_run) == 0:
            _run_cli(["wp-permissions", doc_root], dry_run=dry_run)


def _generate_ssl_flow(dry_run: bool) -> None:
    vhost = _choose_site()
    if not vhost:
        return
    if vhost == "custom":
        domain = _text("Main > Generate SSL certificate > Domain")
        if not domain:
            return
    else:
        domain = vhost.domain
        if vhost.ssl:
            echo_warn("SSL appears configured for this site")
            if not _confirm("Re-issue certificate?", default=False):
                return
    try:
        preflight.ensure_or_fail(
            preflight.checks_for("generate-ssl", domain=domain)
        )
    except SystemExit:
        if _confirm("Run install-lamp now?", default=False):
            _run_cli(["install-lamp"], dry_run=dry_run)
        return
    _run_cli(["generate-ssl", domain], dry_run=dry_run)


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
            wait_choice = _confirm(
                "Main > Install LAMP server > Wait for apt lock?",
                default=True,
            )
            args = [
                "install-lamp",
                "--db-engine",
                engine_choice.lower() if engine_choice != "Auto" else "auto",
                "--wait-apt-lock",
                "120" if wait_choice else "0",
            ]
            if _confirm(
                "Main > Install LAMP server > Set database root password now?",
                default=True,
            ):
                if engine_choice == "MariaDB":
                    echo_info(
                        "MariaDB: root will switch from socket to password authentication."
                    )
                args.append("--set-db-root-pass")
            _run_cli(args, dry_run=dry_run)
            return
        elif choice == "Create a site":
            _create_site_flow(dry_run=dry_run)
        elif choice == "Uninstall site":
            _uninstall_site_flow(dry_run=dry_run)
        elif choice == "Set WordPress permissions":
            _wp_permissions_flow(dry_run=dry_run)
        elif choice == "Generate SSL certificate":
            _generate_ssl_flow(dry_run=dry_run)
        elif choice == "List installed sites":
            if not preflight.has_cmd("apache2").ok or not preflight.apache_paths_present().ok:
                echo_error("Apache not installed. No sites to list.")
            else:
                _list_sites_flow()
        elif choice == "Exit":
            break
