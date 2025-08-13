"""Command line interface for lampkitctl."""
from __future__ import annotations

import click

from . import __version__
from . import db_ops, system_ops, utils, wp_ops


@click.group()
@click.option("--dry-run", is_flag=True, help="Show actions without executing")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, dry_run: bool, verbose: bool) -> None:
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


@cli.command("install-lamp")
@click.pass_context
def install_lamp(ctx: click.Context) -> None:
    """Verify and install LAMP services.

    Args:
        ctx (click.Context): Click context carrying shared state.

    Returns:
        None: This function does not return a value.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["--dry-run", "install-lamp"])
    """
    services = ["apache2", "mysql", "php"]
    dry_run = ctx.obj["dry_run"]
    for srv in services:
        if system_ops.check_service(srv):
            click.echo(f"{srv} already installed")
        else:
            click.echo(f"Installing {srv}...")
            system_ops.install_service(srv, dry_run=dry_run)


@cli.command("create-site")
@click.argument("domain")
@click.option("--doc-root", required=True, help="Document root path")
@click.option("--db-name", required=True, help="Database name")
@click.option("--db-user", required=True, help="Database user")
@click.option("--db-password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--wordpress", is_flag=True, help="Install WordPress")
@click.pass_context
def create_site(
    ctx: click.Context,
    domain: str,
    doc_root: str,
    db_name: str,
    db_user: str,
    db_password: str,
    wordpress: bool,
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
    db_ops.create_database_and_user(
        db_name, db_user, db_password, dry_run=dry_run
    )
    if wordpress:
        wp_ops.install_wordpress(doc_root, db_name, db_user, db_password, dry_run=dry_run)


@cli.command("uninstall-site")
@click.argument("domain")
@click.option("--doc-root", required=True)
@click.option("--db-name", required=True)
@click.option("--db-user", required=True)
@click.pass_context
def uninstall_site(
    ctx: click.Context, domain: str, doc_root: str, db_name: str, db_user: str
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
    db_ops.drop_database_and_user(db_name, db_user, dry_run=dry_run)


@cli.command("list-sites")
def list_sites() -> None:
    """List configured Apache virtual hosts.

    Returns:
        None: This function does not return a value.

    Example:
        >>> runner = CliRunner()
        >>> runner.invoke(cli, ["list-sites"])
    """
    for site in system_ops.list_sites():
        click.echo(f"{site['domain']} -> {site['doc_root']}")


@cli.command("wp-permissions")
@click.argument("doc_root")
@click.pass_context
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
