"""Command line interface for lampkitctl."""
from __future__ import annotations

import functools
import sys
import os
from pathlib import Path
import logging

import click

from . import __version__
from . import db_ops, preflight, preflight_locks, system_ops, utils, wp_ops
from .elevate import maybe_reexec_with_sudo

logger = logging.getLogger(__name__)


@click.group()
@click.option("--dry-run", is_flag=True, help="Show actions without executing")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.option(
    "--non-interactive", is_flag=True, help="Fail fast instead of prompting"
)
@click.pass_context
def cli(ctx: click.Context, dry_run: bool, verbose: bool, non_interactive: bool) -> None:
    """LAMP environment management tool.

    Args:
        ctx (click.Context): Click context carrying shared state.
        dry_run (bool): When ``True`` commands are logged but not executed.
        verbose (bool): Enable verbose logging output.

    Returns:
        None: This function does not return a value.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["--dry-run", "version"])
    """
    utils.setup_logging()
    if verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)
    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run
    ctx.obj["non_interactive"] = non_interactive


def guard(command: str):
    """Decorator to enforce preflight checks for ``command``."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(ctx: click.Context, *args, **kwargs):
            non_interactive = ctx.obj.get("non_interactive", False)
            dry_run = ctx.obj.get("dry_run", False)
            maybe_reexec_with_sudo(
                sys.argv, non_interactive=non_interactive, dry_run=dry_run
            )
            checks = preflight.checks_for(command, **kwargs)
            preflight.ensure_or_fail(
                checks, interactive=not non_interactive, dry_run=dry_run
            )
            return func(ctx, *args, **kwargs)

        return wrapper

    return decorator


@cli.command("install-lamp")
@click.option(
    "--db-engine",
    type=click.Choice(["auto", "mysql", "mariadb"]),
    default="auto",
)
@click.option(
    "--wait-apt-lock",
    type=int,
    default=120,
    show_default=True,
    help="Seconds to wait for APT lock (0 to disable)",
)
@click.option("--set-db-root-pass/--no-set-db-root-pass", default=None)
@click.option("--db-root-pass", default=None, help="Database root password")
@click.option("--db-root-pass-env", default=None, help="Env var with DB root password")
@click.option("--db-root-pass-file", type=click.Path(), default=None, help="File with DB root password")
@click.option(
    "--db-root-plugin",
    type=click.Choice(["default", "mysql_native_password", "caching_sha2_password"]),
    default="default",
    show_default=True,
)
@click.option("--weak-db-root-pass", is_flag=True, help="Allow weak DB root password")
@click.pass_context
def install_lamp(
    ctx: click.Context,
    db_engine: str,
    wait_apt_lock: int,
    set_db_root_pass: bool | None,
    db_root_pass: str | None,
    db_root_pass_env: str | None,
    db_root_pass_file: str | None,
    db_root_plugin: str,
    weak_db_root_pass: bool,
) -> None:
    """Verify and install LAMP services."""

    non_interactive = ctx.obj.get("non_interactive", False)
    dry_run = ctx.obj["dry_run"]
    maybe_reexec_with_sudo(sys.argv, non_interactive=non_interactive, dry_run=dry_run)

    import time

    if wait_apt_lock > 0:
        start = time.time()

        def on_progress(info: preflight_locks.LockInfo) -> None:
            elapsed = int(time.time() - start)
            pid = info.holder_pid or "?"
            cmd = info.holder_cmd or "unknown"
            path = info.path or "unknown"
            click.echo(
                f"\rWaiting for apt lock held by PID {pid} ({cmd}) on {path} ... {elapsed}/{wait_apt_lock}s",
                nl=False,
            )

        info = preflight_locks.wait_for_lock(wait_apt_lock, on_progress=on_progress)
        click.echo("")
        if info.locked:
            raise SystemExit(2)
    else:
        info = preflight_locks.detect_lock()
        if info.locked:
            raise SystemExit(2)

    checks = preflight.checks_for("install-lamp")
    preflight.ensure_or_fail(
        checks, interactive=not non_interactive, dry_run=dry_run
    )
    eng = system_ops.install_lamp_stack(
        None if db_engine == "auto" else db_engine,
        dry_run=dry_run,
    )
    click.echo(f"Database engine: {eng.name} ({eng.server_pkg})")

    password = db_root_pass
    if db_root_pass_env and not password:
        password = os.environ.get(db_root_pass_env)
    if db_root_pass_file and not password:
        path = Path(db_root_pass_file)
        if path.stat().st_mode & 0o077:
            raise SystemExit(2)
        password = path.read_text(encoding="utf-8").splitlines()[0]

    if set_db_root_pass is None:
        if non_interactive:
            set_pass = password is not None
        else:
            set_pass = utils.prompt_yes_no(
                "Set database root password now?", default=True
            )
    else:
        set_pass = set_db_root_pass

    if set_pass and password is None:
        if non_interactive:
            utils.echo_warn("Skipping database root password: no password provided")
            set_pass = False
        else:
            password = click.prompt(
                "Database root password", hide_input=True, confirmation_prompt=True
            )
    elif non_interactive and password is None and set_db_root_pass is not False:
        utils.echo_warn("Skipping database root password: no password provided")

    if set_pass and password and len(password) < 12 and not weak_db_root_pass:
        utils.echo_error(
            "Password must be at least 12 characters. Use --weak-db-root-pass to override."
        )
        raise SystemExit(2)

    if set_pass and password:
        logger.info("install_lamp", extra={"db_root_pass": utils.mask_secret(password)})
        if system_ops.ensure_db_ready(dry_run=dry_run):
            db_ops.set_root_password(eng.name, password, db_root_plugin, dry_run=dry_run)
        else:
            utils.echo_warn("Database server not ready, skipping root password")
    elif password:
        logger.info("install_lamp", extra={"db_root_pass": utils.mask_secret(password)})


@cli.command("create-site")
@click.argument("domain")
@click.option("--doc-root", required=True, help="Document root path")
@click.option("--db-name", required=True, help="Database name")
@click.option("--db-user", required=True, help="Database user")
@click.option("--db-password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--wordpress", is_flag=True, help="Install WordPress")
@click.option(
    "--db-root-auth",
    type=click.Choice(["auto", "password", "socket"]),
    default="auto",
    show_default=True,
)
@click.option("--db-root-pass", default=None, help="Database root password")
@click.pass_context
@guard("create-site")
def create_site(
    ctx: click.Context,
    domain: str,
    doc_root: str,
    db_name: str,
    db_user: str,
    db_password: str,
    wordpress: bool,
    db_root_auth: str,
    db_root_pass: str | None,
) -> None:
    """Create a new site with Apache and MySQL.

    Args:
        ctx (click.Context): Click context carrying shared state.
        domain (str): Domain name for the new site.
        doc_root (str): Document root directory for the site.
        db_name (str): Name of the MySQL database to create.
        db_user (str): MySQL user with access to the database.
        db_password (str): Password for ``db_user``.
        wordpress (bool): If ``True`` install WordPress into the site.

    Returns:
        None: This function does not return a value.

    Example:
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["--dry-run", "create-site", "example.com", "--doc-root=/var/www/example", "--db-name=db", "--db-user=user", "--db-password", "pw"])
    """
    dry_run = ctx.obj["dry_run"]
    system_ops.create_web_directory(doc_root, dry_run=dry_run)
    system_ops.create_virtualhost(domain, doc_root, dry_run=dry_run)
    system_ops.enable_site(domain, dry_run=dry_run)
    system_ops.add_host_entry(domain, dry_run=dry_run)
    auth_mode = db_root_auth
    if auth_mode == "auto":
        auth_mode = "socket" if db_ops.detect_engine() == "mariadb" else "password"
    root_pw = db_root_pass
    if auth_mode == "password" and not root_pw:
        if dry_run:
            root_pw = ""
        elif ctx.obj.get("non_interactive", False):
            raise SystemExit(2)
        else:
            root_pw = click.prompt("Database root password", hide_input=True)
    db_ops.create_database_and_user(
        db_name,
        db_user,
        db_password,
        root_password=root_pw if auth_mode == "password" else None,
        dry_run=dry_run,
    )
    if wordpress:
        wp_ops.install_wordpress(doc_root, db_name, db_user, db_password, dry_run=dry_run)


@cli.command("uninstall-site")
@click.argument("domain")
@click.option("--doc-root", required=True)
@click.option("--db-name", required=True)
@click.option("--db-user", required=True)
@click.option(
    "--db-root-auth",
    type=click.Choice(["auto", "password", "socket"]),
    default="auto",
    show_default=True,
)
@click.option("--db-root-pass", default=None)
@click.pass_context
@guard("uninstall-site")
def uninstall_site(
    ctx: click.Context,
    domain: str,
    doc_root: str,
    db_name: str,
    db_user: str,
    db_root_auth: str,
    db_root_pass: str | None,
) -> None:
    """Remove a site and all related resources.

    Args:
        ctx (click.Context): Click context carrying shared state.
        domain (str): Domain name of the site to remove.
        doc_root (str): Document root path of the site.
        db_name (str): Name of the database to drop.
        db_user (str): Database user to remove.

    Returns:
        None: This function does not return a value.

    Example:
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["--dry-run", "uninstall-site", "example.com", "--doc-root=/var/www/example", "--db-name=db", "--db-user=user"])
    """
    dry_run = ctx.obj["dry_run"]
    if not utils.prompt_confirm(f"Remove site {domain}?", default=False):
        click.echo("Aborted")
        return
    system_ops.remove_virtualhost(domain, dry_run=dry_run)
    system_ops.remove_host_entry(domain, dry_run=dry_run)
    system_ops.remove_web_directory(doc_root, dry_run=dry_run)
    auth_mode = db_root_auth
    if auth_mode == "auto":
        auth_mode = "socket" if db_ops.detect_engine() == "mariadb" else "password"
    root_pw = db_root_pass
    if auth_mode == "password" and not root_pw:
        if dry_run:
            root_pw = ""
        elif ctx.obj.get("non_interactive", False):
            raise SystemExit(2)
        else:
            root_pw = click.prompt("Database root password", hide_input=True)
    db_ops.drop_database_and_user(
        db_name,
        db_user,
        root_password=root_pw if auth_mode == "password" else None,
        dry_run=dry_run,
    )


@cli.command("list-sites")
def list_sites() -> None:
    """List configured Apache virtual hosts.

    Returns:
        None: This function does not return a value.

    Example:
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["list-sites"])
    """
    if not preflight.has_cmd("apache2").ok or not preflight.apache_paths_present().ok:
        click.echo("Apache not installed. No sites to list.")
        return
    for site in system_ops.list_sites():
        click.echo(f"{site['domain']} -> {site['doc_root']}")


@cli.command("wp-permissions")
@click.argument("doc_root")
@click.pass_context
@guard("wp-permissions")
def wp_permissions(ctx: click.Context, doc_root: str) -> None:
    """Set secure WordPress permissions.

    Args:
        ctx (click.Context): Click context carrying shared state.
        doc_root (str): Path to the WordPress installation.

    Returns:
        None: This function does not return a value.

    Example:
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["--dry-run", "wp-permissions", "/var/www/site"])
    """
    dry_run = ctx.obj["dry_run"]
    wp_ops.set_permissions(doc_root, dry_run=dry_run)


@cli.command("generate-ssl")
@click.argument("domain")
@click.pass_context
@guard("generate-ssl")
def generate_ssl(ctx: click.Context, domain: str) -> None:
    """Generate an SSL certificate using certbot.

    Args:
        ctx (click.Context): Click context carrying shared state.
        domain (str): Domain name for the certificate.

    Returns:
        None: This function does not return a value.

    Example:
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["--dry-run", "generate-ssl", "example.com"])
    """
    dry_run = ctx.obj["dry_run"]
    utils.run_command([
        "certbot",
        "--apache",
        "-d",
        domain,
    ], dry_run)


@cli.command("install-launcher")
@click.option(
    "--dir",
    "preferred_dir",
    type=click.Path(file_okay=False),
    help="Install directory (defaults to /usr/local/bin or /opt/homebrew/bin)",
)
@click.option("--force", is_flag=True, help="Overwrite existing launcher")
@click.option("--non-interactive", is_flag=True, help="Fail instead of prompting for sudo")
def install_launcher_cmd(
    preferred_dir: str | None, force: bool, non_interactive: bool
) -> None:
    """Install a sudo-visible launcher that proxies to this venv."""
    maybe_reexec_with_sudo(sys.argv, non_interactive=non_interactive, dry_run=False)
    from .launcher import install_launcher

    path = install_launcher(preferred_dir, force)
    click.echo(f"Installed launcher at: {path}")


@cli.command("uninstall-launcher")
@click.option("--dir", "preferred_dir", type=click.Path(file_okay=False))
@click.option("--non-interactive", is_flag=True)
def uninstall_launcher_cmd(preferred_dir: str | None, non_interactive: bool) -> None:
    """Remove the global sudo launcher."""
    maybe_reexec_with_sudo(sys.argv, non_interactive=non_interactive, dry_run=False)
    from .launcher import uninstall_launcher

    path = uninstall_launcher(preferred_dir)
    click.echo(f"Removed launcher from: {path}")


@cli.command("menu")
@click.pass_context
def menu_cmd(ctx: click.Context) -> None:
    """Launch the interactive text-based menu.

    Args:
        ctx (click.Context): Click context carrying shared state.
    """
    from . import menu as menu_module

    dry_run = ctx.obj["dry_run"]
    menu_module.run_menu(dry_run=dry_run)


@cli.command("version")
def version_cmd() -> None:
    """Show version information.

    Returns:
        None: This function does not return a value.

    Example:
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["version"])
    """
    click.echo(__version__)


def main() -> None:
    """Entry point for executing the CLI directly.

    Returns:
        None: This function does not return a value.

    Example:
        >>> main()
    """
    cli()
