"""WordPress related operations."""
from __future__ import annotations

import logging
from pathlib import Path

from .utils import run_command

logger = logging.getLogger(__name__)


WORDPRESS_URL = "https://wordpress.org/latest.tar.gz"


def download_wordpress(target_dir: str, dry_run: bool = False) -> None:
    """Download and extract the latest WordPress package.

    Args:
        target_dir (str): Directory where WordPress should be downloaded and
            extracted.
        dry_run (bool, optional): If ``True`` the commands are logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If a command fails and ``dry_run`` is
            ``False``.

    Example:
        >>> download_wordpress("/var/www", dry_run=True)
    """
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
    """Install WordPress into ``doc_root`` and configure the database.

    Args:
        doc_root (str): Target directory for the WordPress installation.
        db_name (str): Name of the MySQL database.
        db_user (str): Database username.
        db_password (str): Database user password.
        dry_run (bool, optional): If ``True`` the commands are logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If configuration files cannot be read or written and
            ``dry_run`` is ``False``.

    Example:
        >>> install_wordpress("/var/www", "db", "user", "pw", dry_run=True)
    """
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
    """Set secure file permissions for a WordPress installation.

    Args:
        doc_root (str): Path to the WordPress installation.
        owner (str, optional): Owner and group for the files. Defaults to
            ``"www-data"``.
        dry_run (bool, optional): If ``True`` the commands are logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If a command fails and ``dry_run`` is
            ``False``.

    Example:
        >>> set_permissions("/var/www/site", dry_run=True)
    """
    path = Path(doc_root)
    run_command(["chown", "-R", f"{owner}:{owner}", str(path)], dry_run)
    run_command(["find", str(path), "-type", "d", "-exec", "chmod", "755", "{}", ";"], dry_run)
    run_command(["find", str(path), "-type", "f", "-exec", "chmod", "644", "{}", ";"], dry_run)
