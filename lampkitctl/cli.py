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
    """LAMP environment management tool."""
    utils.setup_logging()
    if verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)
    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run


@cli.command("install-lamp")
@click.pass_context
def install_lamp(ctx: click.Context) -> None:
    """Verify and install LAMP services."""
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
    """Create a new site with Apache and MySQL."""
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
    """Remove a site and all related resources."""
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
    """List configured Apache virtual hosts."""
    for site in system_ops.list_sites():
        click.echo(f"{site['domain']} -> {site['doc_root']}")


@cli.command("wp-permissions")
@click.argument("doc_root")
@click.pass_context
def wp_permissions(ctx: click.Context, doc_root: str) -> None:
    """Set secure WordPress permissions."""
    dry_run = ctx.obj["dry_run"]
    wp_ops.set_permissions(doc_root, dry_run=dry_run)


@cli.command("generate-ssl")
@click.argument("domain")
@click.pass_context
def generate_ssl(ctx: click.Context, domain: str) -> None:
    """Generate an SSL certificate using certbot."""
    dry_run = ctx.obj["dry_run"]
    utils.run_command([
        "certbot",
        "--apache",
        "-d",
        domain,
    ], dry_run)


@cli.command("version")
def version_cmd() -> None:
    """Show version."""
    click.echo(__version__)


def main() -> None:
    cli()
