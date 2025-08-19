"""Database operations for lampkitctl."""
from __future__ import annotations
import logging
import subprocess
from typing import Optional

from .utils import run_command
import textwrap
import os

logger = logging.getLogger(__name__)


class DBEngine:
    MYSQL = "mysql"
    MARIADB = "mariadb"


def _exec_sql_as_root(sql: str, *, dry_run: bool = False) -> None:
    """Execute ``sql`` as the local root user via socket."""

    run_command(
        ["bash", "-lc", "mysql --protocol=socket -u root"],
        dry_run=dry_run,
        input_text=sql,
    )


def set_root_password(
    engine: str, password: str, plugin: str = "default", *, dry_run: bool = False
) -> None:
    """Set the database root password for ``engine``."""

    if engine == DBEngine.MARIADB:
        sql = textwrap.dedent(
            f"""
            ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('{password}');
            FLUSH PRIVILEGES;
            """
        )
        _exec_sql_as_root(sql, dry_run=dry_run)
        return

    auth = None
    if plugin == "mysql_native_password":
        auth = "mysql_native_password"
    elif plugin == "caching_sha2_password":
        auth = "caching_sha2_password"
    if auth:
        sql = (
            f"ALTER USER 'root'@'localhost' IDENTIFIED WITH {auth} BY '{password}'; FLUSH PRIVILEGES;"
        )
    else:
        sql = (
            f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{password}'; FLUSH PRIVILEGES;"
        )
    _exec_sql_as_root(sql, dry_run=dry_run)


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
    cmd = ["mysql", "-u", root_user, "-e", sql]
    log_cmd = ["mysql", "-u", root_user, "-e", "<SQL>"]
    env = None
    if root_password:
        env = os.environ.copy()
        env["MYSQL_PWD"] = root_password
    run_command(cmd, dry_run, log_cmd=log_cmd, env=env)


def drop_database_and_user(
    db_name: str,
    user: str,
    *,
    root_user: str = "root",
    root_password: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Remove a MySQL database and its user.

    ``user`` may include an optional host (``user@host``). When no host is
    provided, ``localhost`` is assumed. The database is dropped if it exists
    and the associated user is removed along with its privileges.

    Args:
        db_name (str): Name of the database to drop.
        user (str): Username to remove, optionally with host.
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
    if "@" in user:
        user_name, host = user.split("@", 1)
    else:
        user_name, host = user, "localhost"
    sql = (
        f"DROP DATABASE IF EXISTS `{db_name}`;"
        f" DROP USER IF EXISTS '{user_name}'@'{host}';"
        " FLUSH PRIVILEGES;"
    )
    cmd = ["mysql", "-u", root_user, "-e", sql]
    log_cmd = ["mysql", "-u", root_user, "-e", "<SQL>"]
    env = None
    if root_password:
        env = os.environ.copy()
        env["MYSQL_PWD"] = root_password
    run_command(cmd, dry_run, log_cmd=log_cmd, env=env)
