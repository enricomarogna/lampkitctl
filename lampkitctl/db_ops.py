"""Database operations for lampkitctl."""
from __future__ import annotations

import logging
from typing import Optional

from .utils import run_command

logger = logging.getLogger(__name__)


def create_database_and_user(
    db_name: str,
    user: str,
    password: str,
    *,
    root_user: str = "root",
    root_password: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Create a database and user with full privileges."""
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
    """Drop database and user."""
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
