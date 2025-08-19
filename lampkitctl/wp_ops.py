"""WordPress related operations."""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from .utils import run_command, echo_warn, echo_error

logger = logging.getLogger(__name__)


WORDPRESS_URL = "https://wordpress.org/latest.tar.gz"


def download_wordpress(target_dir: str, dry_run: bool = False) -> None:
    """Download and extract the latest WordPress package into ``target_dir``.

    The archive is fetched to a temporary location and extracted with
    ``--strip-components=1`` so that files land directly in ``target_dir``.
    The temporary archive is removed afterwards.
    """

    tar_path = Path(tempfile.gettempdir()) / f"wordpress-{os.getpid()}.tar.gz"
    run_command(["wget", "-q", WORDPRESS_URL, "-O", str(tar_path)], dry_run)
    run_command(
        [
            "tar",
            "-xzf",
            str(tar_path),
            "-C",
            target_dir,
            "--strip-components=1",
            "--no-same-owner",
            "--overwrite-dir",
        ],
        dry_run,
    )
    run_command(["rm", "-f", str(tar_path)], dry_run)


def install_wordpress(
    doc_root: str,
    db_name: str,
    db_user: str,
    db_password: str,
    dry_run: bool = False,
) -> None:
    """Install WordPress into ``doc_root`` and configure the database."""

    config = Path(doc_root) / "wp-config.php"
    if config.exists():
        echo_warn("WordPress appears to be installed; skipping files extraction.")
    else:
        try:
            download_wordpress(doc_root, dry_run)
        except SystemExit:
            echo_error("Failed to download or extract WordPress. Aborting.")
            raise
        sample = Path(doc_root) / "wp-config-sample.php"
        if dry_run:
            logger.info("configure_wp", extra={"path": str(config)})
        else:
            text = sample.read_text()
            text = (
                text.replace("database_name_here", db_name)
                .replace("username_here", db_user)
                .replace("password_here", db_password)
            )
            config.write_text(text)
    set_permissions(doc_root, dry_run=dry_run)


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
