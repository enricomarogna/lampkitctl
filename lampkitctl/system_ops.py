"""Operations related to system services and file management."""
from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path
from typing import List

from .packages import (
    APACHE_PKG,
    CERTBOT_PKGS,
    PHP_BASE,
    PHP_EXTRAS,
    detect_db_engine as _detect_pkg_db_engine,
    refresh_cache,
    detect_pkg_status,
)

# Re-export for backward compatibility
detect_db_engine = _detect_pkg_db_engine
from .utils import run_command, atomic_append
from . import preflight_locks

logger = logging.getLogger(__name__)


# Packages comprising the LAMP stack (minus the DB engine).
LAMP_BASE = [APACHE_PKG, *PHP_BASE, *PHP_EXTRAS, *CERTBOT_PKGS]
DB_MAP = {"mysql": "mysql-server", "mariadb": "mariadb-server"}


def compute_lamp_packages(db_engine: str) -> list[str]:
    """Return package list for ``db_engine`` plus core LAMP components."""

    return [DB_MAP[db_engine]] + LAMP_BASE


def install_or_update_lamp(
    db_engine: str,
    *,
    dry_run: bool = False,
    wait_lock: int | None = None,
    refresh: bool = True,
) -> None:
    """Install or update the LAMP stack depending on package status."""

    if wait_lock and wait_lock > 0:
        info = preflight_locks.wait_for_lock(wait_lock)
        if info.locked:
            raise SystemExit(2)
    elif wait_lock == 0:
        if preflight_locks.detect_lock().locked:
            raise SystemExit(2)

    pkgs = compute_lamp_packages(db_engine)
    if refresh:
        run_command(["apt-get", "update"], dry_run)
    status = detect_pkg_status(pkgs)

    if status.missing:
        logger.info(
            "install_lamp_stack",
            extra={"packages": pkgs, "db_engine": db_engine, "dry_run": dry_run},
        )
        run_command(
            ["apt-get", "install", "-y", "--no-install-recommends", *pkgs], dry_run
        )
        return

    if status.upgradable:
        logger.info(
            "update_lamp_stack",
            extra={"packages": status.upgradable, "db_engine": db_engine, "dry_run": dry_run},
        )
        run_command(
            ["apt-get", "install", "-y", "--only-upgrade", *status.upgradable], dry_run
        )
        return

    logger.info(
        "lamp_stack_uptodate",
        extra={"packages": pkgs, "db_engine": db_engine, "dry_run": dry_run},
    )

def ensure_db_ready(retries: int = 5, delay: float = 1.0, dry_run: bool = False) -> bool:
    """Return ``True`` when the database server responds to ``SELECT 1``."""

    if dry_run:
        return True
    for _ in range(retries):
        proc = run_command(
            ["mysql", "--protocol=socket", "-u", "root", "-e", "SELECT 1"],
            dry_run=False,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return True
        time.sleep(delay)
    return False


def install_lamp_stack(
    pkgs: list[str], *, dry_run: bool = False
) -> None:
    """Install missing LAMP packages."""

    logger.info(
        "install_lamp_stack", extra={"packages": pkgs, "dry_run": dry_run}
    )
    run_command(
        ["apt-get", "install", "-y", "--no-install-recommends", *pkgs], dry_run
    )


def update_lamp_stack(upgradable: list[str], *, dry_run: bool = False) -> None:
    """Upgrade existing LAMP packages."""

    logger.info(
        "update_lamp_stack", extra={"upgradable": upgradable, "dry_run": dry_run}
    )
    run_command(
        ["apt-get", "install", "-y", "--only-upgrade", *upgradable], dry_run
    )


def reinstall_lamp_stack(pkgs: list[str], *, dry_run: bool = False) -> None:
    """Reinstall LAMP packages."""

    logger.info(
        "reinstall_lamp_stack", extra={"packages": pkgs, "dry_run": dry_run}
    )
    run_command(["apt-get", "install", "-y", "--reinstall", *pkgs], dry_run)


def install_lamp_stack_full(
    preferred_engine: str | None,
    with_php: bool = True,
    with_certbot: bool = True,
    dry_run: bool = False,
    no_recommends: bool = True,
    wait_apt_lock: int = 0,
):
    """Install Apache, a database engine and optional PHP/Certbot packages."""

    if wait_apt_lock > 0:
        info = preflight_locks.wait_for_lock(wait_apt_lock)
        if info.locked:
            raise SystemExit(2)
    else:
        if preflight_locks.detect_lock().locked:
            raise SystemExit(2)

    refresh_cache(dry_run=dry_run)
    eng = detect_db_engine(preferred_engine)
    pkgs = [APACHE_PKG, eng.server_pkg]
    if with_php:
        pkgs += PHP_BASE + PHP_EXTRAS
    if with_certbot:
        pkgs += CERTBOT_PKGS
    logger.info(
        "install_lamp_stack_full",
        extra={"packages": pkgs, "db_engine": eng.name, "dry_run": dry_run},
    )
    install_cmd = ["apt-get", "install", "-y"]
    if no_recommends:
        install_cmd.append("--no-install-recommends")
    install_cmd.extend(pkgs)
    run_command(install_cmd, dry_run=dry_run, capture_output=True)
    return eng


def check_service(service: str) -> bool:
    """Check whether a system service is installed.

    Args:
        service (str): Name of the service executable to search for.

    Returns:
        bool: ``True`` if the service is available in the ``PATH``;
            otherwise ``False``.

    Example:
        >>> check_service("apache2")
        True
    """
    return shutil.which(service) is not None


def install_service(service: str, dry_run: bool = False) -> None:
    """Install a system service using ``apt-get``.

    Args:
        service (str): Name of the package to install.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If the installation command fails and
            ``dry_run`` is ``False``.

    Example:
        >>> install_service("apache2", dry_run=True)
    """
    cmd = ["apt-get", "install", "-y", service]
    run_command(["apt-get", "update"], dry_run, capture_output=True)
    run_command(cmd, dry_run, capture_output=True)


def create_web_directory(path: str, dry_run: bool = False) -> None:
    """Create the document root for a website.

    The directory is owned by ``www-data:www-data``. The invoking user is added
    to the ``www-data`` group if needed.
    """

    run_command(["mkdir", "-p", path], dry_run)
    run_command(["chown", "-R", "www-data:www-data", path], dry_run)
    user = os.environ.get("SUDO_USER") or os.environ.get("USER")
    if user and user != "root":
        try:
            import grp
            import pwd

            groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
            gid = pwd.getpwnam(user).pw_gid
            groups.append(grp.getgrgid(gid).gr_name)
            in_group = "www-data" in groups
        except Exception:  # pragma: no cover - system specific
            in_group = True
        if not in_group:
            run_command(["usermod", "-a", "-G", "www-data", user], dry_run)
            print(
                f"Added {user} to www-data group. You may need to log out and back in."
            )


def create_virtualhost(
    domain: str,
    doc_root: str,
    sites_available: str = "/etc/apache2/sites-available",
    dry_run: bool = False,
) -> Path:
    """Create an Apache virtual host configuration file.

    Args:
        domain (str): Domain name served by the virtual host.
        doc_root (str): Path to the site document root.
        sites_available (str, optional): Directory where configuration files
            are stored. Defaults to ``"/etc/apache2/sites-available"``.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False``.

    Returns:
        Path: Path to the generated configuration file.

    Raises:
        OSError: If the configuration file cannot be written and ``dry_run``
            is ``False``.

    Example:
        >>> create_virtualhost("example.com", "/var/www/example", dry_run=True)
        PosixPath('/etc/apache2/sites-available/example.com.conf')
    """
    config = f"""
<VirtualHost *:80>
    ServerName {domain}
    DocumentRoot {doc_root}
    <Directory {doc_root}>
        AllowOverride All
        Require all granted
    </Directory>
    ErrorLog ${{APACHE_LOG_DIR}}/{domain}_error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain}_access.log combined
</VirtualHost>
"""
    conf_path = Path(sites_available) / f"{domain}.conf"
    if dry_run:
        logger.info("create_virtualhost", extra={"path": str(conf_path)})
        return conf_path
    conf_path.write_text(config)
    return conf_path


def enable_site(domain: str, dry_run: bool = False) -> None:
    """Enable an Apache site and reload the server.

    Args:
        domain (str): Domain name of the site to enable.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If a command fails and ``dry_run`` is
            ``False``.

    Example:
        >>> enable_site("example.com", dry_run=True)
    """
    run_command(["a2ensite", domain], dry_run)
    run_command(["systemctl", "reload", "apache2"], dry_run)


def add_host_entry(domain: str, ip: str = "127.0.0.1", hosts_file: str = "/etc/hosts", dry_run: bool = False) -> None:
    """Append a host entry to the ``/etc/hosts`` file.

    Args:
        domain (str): Hostname to associate with the IP address.
        ip (str, optional): IP address to map to ``domain``. Defaults to
            ``"127.0.0.1"``.
        hosts_file (str, optional): Path to the hosts file. Defaults to
            ``"/etc/hosts"``.
        dry_run (bool, optional): If ``True`` the change is logged but not
            written. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If the file cannot be written and ``dry_run`` is ``False``.

    Example:
        >>> add_host_entry("example.com", hosts_file="/tmp/hosts", dry_run=True)
    """
    entry = f"{ip} {domain}\n"
    if dry_run:
        logger.info("add_host_entry", extra={"entry": entry.strip()})
        return
    atomic_append(hosts_file, entry)


def list_sites(sites_available: str = "/etc/apache2/sites-available") -> List[dict]:
    """List configured Apache virtual hosts.

    Args:
        sites_available (str, optional): Directory containing Apache
            configuration files. Defaults to
            ``"/etc/apache2/sites-available"``.

    Returns:
        List[dict]: A list of dictionaries with ``domain`` and ``doc_root``
        keys describing each virtual host.

    Example:
        >>> list_sites("/etc/apache2/sites-available")
        [{'domain': 'example.com', 'doc_root': '/var/www/example'}]
    """
    results: List[dict] = []
    for conf_file in Path(sites_available).glob("*.conf"):
        domain = conf_file.stem
        doc_root = ""
        try:
            for line in conf_file.read_text().splitlines():
                if line.strip().startswith("DocumentRoot"):
                    doc_root = line.split()[1]
                    break
        except OSError:
            continue
        results.append({"domain": domain, "doc_root": doc_root})
    return results


def remove_virtualhost(
    domain: str,
    sites_available: str = "/etc/apache2/sites-available",
    dry_run: bool = False,
) -> None:
    """Delete an Apache virtual host configuration file.

    Args:
        domain (str): Domain name whose configuration should be removed.
        sites_available (str, optional): Directory containing Apache
            configuration files. Defaults to
            ``"/etc/apache2/sites-available"``.
        dry_run (bool, optional): If ``True`` the action is logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If the file cannot be removed and ``dry_run`` is ``False``.

    Example:
        >>> remove_virtualhost("example.com", dry_run=True)
    """
    conf_path = Path(sites_available) / f"{domain}.conf"
    if dry_run:
        logger.info("remove_virtualhost", extra={"path": str(conf_path)})
        return
    try:
        conf_path.unlink()
    except FileNotFoundError:
        logger.warning("virtualhost_not_found", extra={"path": str(conf_path)})


def remove_web_directory(path: str, dry_run: bool = False) -> None:
    """Remove the document root directory for a site.

    Args:
        path (str): Path to the directory to remove.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False".

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If removal fails and ``dry_run`` is
            ``False``.

    Example:
        >>> remove_web_directory("/var/www/example", dry_run=True)
    """
    run_command(["rm", "-rf", path], dry_run)


def remove_host_entry(domain: str, hosts_file: str = "/etc/hosts", dry_run: bool = False) -> None:
    """Remove a host entry from ``/etc/hosts``.

    Args:
        domain (str): Hostname to remove.
        hosts_file (str, optional): Path to the hosts file. Defaults to
            ``"/etc/hosts"``.
        dry_run (bool, optional): If ``True`` the change is logged but not
            written. Defaults to ``False".

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If the hosts file cannot be modified and ``dry_run`` is
            ``False".

    Example:
        >>> remove_host_entry("example.com", hosts_file="/tmp/hosts", dry_run=True)
    """
    if dry_run:
        logger.info("remove_host_entry", extra={"domain": domain})
        return
    if not os.path.exists(hosts_file):
        return
    path = Path(hosts_file)
    lines = path.read_text(encoding="utf-8").splitlines(True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for line in lines:
            if domain not in line:
                fh.write(line)
    os.chmod(tmp, path.stat().st_mode)
    os.replace(tmp, path)
