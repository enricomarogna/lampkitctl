"""WordPress related operations."""
from __future__ import annotations

import logging
from pathlib import Path

from .utils import run_command

logger = logging.getLogger(__name__)


WORDPRESS_URL = "https://wordpress.org/latest.tar.gz"


def download_wordpress(target_dir: str, dry_run: bool = False) -> None:
    """Download and extract WordPress into target directory."""
    tar_path = str(Path(target_dir) / "wordpress.tar.gz")
    run_command(["wget", "-q", WORDPRESS_URL, "-O", tar_path], dry_run)
    run_command(["tar", "-xzf", tar_path, "-C", target_dir], dry_run)


def install_wordpress(
    doc_root: str,
    db_name: str,
    db_user: str,
    db_password: str,
    dry_run: bool = False,
) -> None:
    """Install WordPress into ``doc_root``."""
    download_wordpress(doc_root, dry_run)
    sample = Path(doc_root) / "wordpress" / "wp-config-sample.php"
    config = Path(doc_root) / "wordpress" / "wp-config.php"
    if dry_run:
        logger.info("configure_wp", extra={"path": str(config)})
        return
    text = sample.read_text()
    text = (
        text.replace("database_name_here", db_name)
        .replace("username_here", db_user)
        .replace("password_here", db_password)
    )
    config.write_text(text)


def set_permissions(doc_root: str, owner: str = "www-data", dry_run: bool = False) -> None:
    """Set secure permissions for a WordPress installation."""
    path = Path(doc_root)
    run_command(["chown", "-R", f"{owner}:{owner}", str(path)], dry_run)
    run_command(["find", str(path), "-type", "d", "-exec", "chmod", "755", "{}", ";"], dry_run)
    run_command(["find", str(path), "-type", "f", "-exec", "chmod", "644", "{}", ";"], dry_run)
