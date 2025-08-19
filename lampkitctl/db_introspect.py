from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

SYSTEM_SCHEMAS = {"information_schema", "mysql", "performance_schema", "sys"}

_CACHED_ROOT_PASSWORD: Optional[str] = None


class DBListError(RuntimeError):
    """Raised when database listing fails."""


def _env_with_pwd(pwd: Optional[str]) -> dict:
    env = os.environ.copy()
    p = pwd or env.get("LAMPKITCTL_DB_ROOT_PASS") or _CACHED_ROOT_PASSWORD
    if p:
        env["MYSQL_PWD"] = p
    return env


_DEF_CMD_SOCKET = [
    "mysql",
    "--protocol=socket",
    "-u",
    "root",
    "-N",
    "-B",
    "-e",
    "SHOW DATABASES",
]
_DEF_CMD_TCP = [
    "mysql",
    "-h",
    "127.0.0.1",
    "-P",
    "3306",
    "-u",
    "root",
    "-N",
    "-B",
    "-e",
    "SHOW DATABASES",
]

_SUDO_CMD_SOCKET = [
    "sudo",
    "-S",
    "mysql",
    "--protocol=socket",
    "-u",
    "root",
    "-N",
    "-B",
    "-e",
    "SHOW DATABASES",
]
_SUDO_CMD_DCNF = [
    "sudo",
    "-S",
    "mysql",
    "--defaults-file=/etc/mysql/debian.cnf",
    "-N",
    "-B",
    "-e",
    "SHOW DATABASES",
]


def _parse_names(output: str) -> list[str]:
    names = [ln.strip() for ln in output.splitlines() if ln.strip()]
    return sorted(n for n in names if n not in SYSTEM_SCHEMAS)


def cache_root_password(pwd: str) -> None:
    global _CACHED_ROOT_PASSWORD
    _CACHED_ROOT_PASSWORD = pwd


def list_databases(password: Optional[str] = None) -> list[str]:
    env = _env_with_pwd(password)
    last_err: Optional[Exception] = None

    for cmd in (_DEF_CMD_SOCKET, _DEF_CMD_TCP):
        try:
            out = subprocess.check_output(cmd, env=env, text=True, stderr=subprocess.STDOUT)
            return _parse_names(out)
        except Exception as exc:  # pragma: no cover - error path
            last_err = exc

    raise DBListError(str(last_err) if last_err else "DB list failed")


def list_databases_with_sudo(sudo_password: str) -> list[str]:
    last_err: Optional[Exception] = None
    for cmd in (_SUDO_CMD_SOCKET, _SUDO_CMD_DCNF):
        try:
            proc = subprocess.run(
                cmd,
                input=f"{sudo_password}\n",
                text=True,
                check=True,
                capture_output=True,
            )
            return _parse_names(proc.stdout)
        except Exception as exc:  # pragma: no cover - error path
            last_err = exc
    raise DBListError(str(last_err) if last_err else "DB sudo list failed")


# ---------------------------------------------------------------------------
# User listing
# ---------------------------------------------------------------------------

SYSTEM_USERS = {"mysql.sys", "mysql.session", "debian-sys-maint"}
HIDE_USERS = SYSTEM_USERS | {"root"}


@dataclass
class DBUsers:
    items: list[str]  # values like "user@host"


_DEF_SQL_USERS = (
    "SELECT CONCAT(User, '@', Host) FROM mysql.user ORDER BY User, Host;",
)

_DEF_CMD_SOCKET_USERS = [
    "mysql",
    "--protocol=socket",
    "-u",
    "root",
    "-N",
    "-B",
    "-e",
    _DEF_SQL_USERS[0],
]
_DEF_CMD_TCP_USERS = [
    "mysql",
    "-h",
    "127.0.0.1",
    "-P",
    "3306",
    "-u",
    "root",
    "-N",
    "-B",
    "-e",
    _DEF_SQL_USERS[0],
]

_SUDO_CMD_SOCKET_USERS = [
    "sudo",
    "-S",
    "mysql",
    "--protocol=socket",
    "-u",
    "root",
    "-N",
    "-B",
    "-e",
    _DEF_SQL_USERS[0],
]
_SUDO_CMD_DCNF_USERS = [
    "sudo",
    "-S",
    "mysql",
    "--defaults-file=/etc/mysql/debian.cnf",
    "-N",
    "-B",
    "-e",
    _DEF_SQL_USERS[0],
]


class DBUserListError(RuntimeError):
    pass


_DEF_PARSE = lambda out: sorted(
    u
    for u in (ln.strip() for ln in out.splitlines() if ln.strip())
    if u.split("@", 1)[0] not in HIDE_USERS
)


def list_users(password: Optional[str] = None) -> DBUsers:
    env = _env_with_pwd(password)
    last_err: Optional[Exception] = None
    for cmd in (_DEF_CMD_SOCKET_USERS, _DEF_CMD_TCP_USERS):
        try:
            out = subprocess.check_output(
                cmd, env=env, text=True, stderr=subprocess.STDOUT
            )
            return DBUsers(_DEF_PARSE(out))
        except Exception as exc:  # pragma: no cover - error path
            last_err = exc
    raise DBUserListError(str(last_err) if last_err else "DB user list failed")


def list_users_with_sudo(sudo_password: str) -> DBUsers:
    last_err: Optional[Exception] = None
    for cmd in (_SUDO_CMD_SOCKET_USERS, _SUDO_CMD_DCNF_USERS):
        try:
            proc = subprocess.run(
                cmd,
                input=f"{sudo_password}\n",
                text=True,
                check=True,
                capture_output=True,
            )
            return DBUsers(_DEF_PARSE(proc.stdout))
        except Exception as exc:  # pragma: no cover - error path
            last_err = exc
    raise DBUserListError(
        str(last_err) if last_err else "DB user sudo list failed"
    )


WP_DB_NAME_RE = re.compile(r"define\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
WP_DB_USER_RE = re.compile(r"define\(\s*['\"]DB_USER['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
WP_DB_HOST_RE = re.compile(r"define\(\s*['\"]DB_HOST['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
WP_TABLE_PREFIX_RE = re.compile(r"^\s*\$table_prefix\s*=\s*['\"]([^'\"]+)['\"];", re.MULTILINE)


@dataclass
class WPConfig:
    name: str | None
    user: str | None
    host: str | None
    table_prefix: str | None


def parse_wp_config(docroot: str) -> WPConfig | None:
    path = os.path.join(docroot, "wp-config.php")
    if not os.path.exists(path):
        return None
    try:
        data = open(path, "r", encoding="utf-8", errors="ignore").read()
    except Exception:
        return None
    name = (WP_DB_NAME_RE.search(data) or [None, None])[1]
    user = (WP_DB_USER_RE.search(data) or [None, None])[1]
    host = (WP_DB_HOST_RE.search(data) or [None, None])[1]
    pref_m = WP_TABLE_PREFIX_RE.search(data)
    prefix = pref_m.group(1) if pref_m else None
    return WPConfig(name, user, host, prefix)

