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
    """Return True if the given service is installed."""
    return shutil.which(service) is not None


def install_service(service: str, dry_run: bool = False) -> None:
    """Install a system service using apt-get."""
    cmd = ["apt-get", "install", "-y", service]
    run_command(["apt-get", "update"], dry_run)
    run_command(cmd, dry_run)


def create_web_directory(path: str, dry_run: bool = False) -> None:
    """Create the web directory for the site."""
    run_command(["mkdir", "-p", path], dry_run)


def create_virtualhost(domain: str, doc_root: str, sites_available: str = "/etc/apache2/sites-available", dry_run: bool = False) -> Path:
    """Create an Apache virtualhost configuration file."""
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
    """Enable an Apache site."""
    run_command(["a2ensite", domain], dry_run)
    run_command(["systemctl", "reload", "apache2"], dry_run)


def add_host_entry(domain: str, ip: str = "127.0.0.1", hosts_file: str = "/etc/hosts", dry_run: bool = False) -> None:
    """Add an entry to /etc/hosts."""
    entry = f"{ip} {domain}\n"
    if dry_run:
        logger.info("add_host_entry", extra={"entry": entry.strip()})
        return
    with open(hosts_file, "a", encoding="utf-8") as fh:
        fh.write(entry)


def list_sites(sites_available: str = "/etc/apache2/sites-available") -> List[dict]:
    """List configured Apache sites."""
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


def remove_virtualhost(domain: str, sites_available: str = "/etc/apache2/sites-available", dry_run: bool = False) -> None:
    """Remove Apache virtualhost configuration."""
    conf_path = Path(sites_available) / f"{domain}.conf"
    if dry_run:
        logger.info("remove_virtualhost", extra={"path": str(conf_path)})
        return
    try:
        conf_path.unlink()
    except FileNotFoundError:
        logger.warning("virtualhost_not_found", extra={"path": str(conf_path)})


def remove_web_directory(path: str, dry_run: bool = False) -> None:
    """Remove the web directory."""
    run_command(["rm", "-rf", path], dry_run)


def remove_host_entry(domain: str, hosts_file: str = "/etc/hosts", dry_run: bool = False) -> None:
    """Remove entry from /etc/hosts."""
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
