"""Database operations for lampkitctl."""
from __future__ import annotations

import logging
import subprocess
from typing import Optional

from .utils import run_command

logger = logging.getLogger(__name__)


def detect_engine() -> str:
    """Return the installed database engine name (``mysql`` or ``mariadb``)."""

    try:
        p = subprocess.run(["mysql", "--version"], capture_output=True, text=True)
    except OSError:
        return "mysql"
    out = (p.stdout or "") + (p.stderr or "")
    return "mariadb" if "mariadb" in out.lower() else "mysql"


def create_database_and_user(
    db_name: str,
    user: str,
    password: str,
    *,
    root_user: str = "root",
    root_password: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Create a MySQL database and associated user.

    This function executes a series of SQL commands to create a database
    if it does not already exist, create a user and grant that user full
    privileges on the new database.

    Args:
        db_name (str): Name of the database to create.
        user (str): Username for the new database user.
        password (str): Password for the new user.
        root_user (str, optional): MySQL root username used to execute the
            SQL commands. Defaults to "root".
        root_password (Optional[str], optional): Password for ``root_user``.
            If provided, it is passed to the MySQL client. Defaults to ``None``.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If the underlying command fails and
            ``dry_run`` is ``False``.

    Example:
        >>> create_database_and_user("blog", "blog_user", "s3cr3t", dry_run=True)
    """
    sql = (
        f"CREATE DATABASE IF NOT EXISTS `{db_name}`;"
        f" CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{password}';"
        f" GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{user}'@'localhost';"
        " FLUSH PRIVILEGES;"
    )
    cmd = ["mysql", "-u", root_user]
    log_cmd = ["mysql", "-u", root_user]
    if root_password:
        cmd.append(f"-p{root_password}")
        log_cmd.append("-p******")
    cmd.extend(["-e", sql])
    log_cmd.extend(["-e", "<SQL>"])
    run_command(cmd, dry_run, log_cmd=log_cmd)


def drop_database_and_user(
    db_name: str,
    user: str,
    *,
    root_user: str = "root",
    root_password: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Remove a MySQL database and its user.

    The database is dropped if it exists and the associated user is removed
    along with its privileges.

    Args:
        db_name (str): Name of the database to drop.
        user (str): Username to remove.
        root_user (str, optional): MySQL root username used to execute the
            SQL commands. Defaults to "root".
        root_password (Optional[str], optional): Password for ``root_user``.
            If provided, it is passed to the MySQL client. Defaults to ``None``.
        dry_run (bool, optional): If ``True`` the command is logged but not
            executed. Defaults to ``False``.

    Returns:
        None: This function does not return a value.

    Raises:
        subprocess.CalledProcessError: If the underlying command fails and
            ``dry_run`` is ``False``.

    Example:
        >>> drop_database_and_user("blog", "blog_user", dry_run=True)
    """
    sql = (
        f"DROP DATABASE IF EXISTS `{db_name}`;"
        f" DROP USER IF EXISTS '{user}'@'localhost';"
        " FLUSH PRIVILEGES;"
    )
    cmd = ["mysql", "-u", root_user]
    log_cmd = ["mysql", "-u", root_user]
    if root_password:
        cmd.append(f"-p{root_password}")
        log_cmd.append("-p******")
    cmd.extend(["-e", sql])
    log_cmd.extend(["-e", "<SQL>"])
    run_command(cmd, dry_run, log_cmd=log_cmd)
