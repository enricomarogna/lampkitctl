"""Operations related to system services and file management."""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import List

from .utils import run_command

logger = logging.getLogger(__name__)


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

    Args:
        path (str): Directory path to create.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If the directory creation fails and
            ``dry_run`` is ``False``.

    Example:
        >>> create_web_directory("/var/www/example", dry_run=True)
    """
    run_command(["mkdir", "-p", path], dry_run)


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
    with open(hosts_file, "a", encoding="utf-8") as fh:
        fh.write(entry)


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
    with open(hosts_file, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    with open(hosts_file, "w", encoding="utf-8") as fh:
        for line in lines:
            if domain not in line:
                fh.write(line)
