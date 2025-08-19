from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import os, re, subprocess, shlex

SYSTEM_SCHEMAS = {"information_schema", "mysql", "performance_schema", "sys"}

# Cached password for the session (process lifetime only)
_CACHED_ROOT_PASSWORD: Optional[str] = None


@dataclass
class DBList:
    databases: list[str]


def _env_with_pwd(pwd: Optional[str]) -> dict:
    env = os.environ.copy()
    p = pwd or env.get("LAMPKITCTL_DB_ROOT_PASS") or _CACHED_ROOT_PASSWORD
    if p:
        env["MYSQL_PWD"] = p
    return env


class DBListError(RuntimeError):
    pass


_ATTEMPTS = (
    ["mysql", "--protocol=socket", "-u", "root", "-N", "-B", "-e", "SHOW DATABASES"],
    [
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
    ],
)


_SUDO_ATTEMPTS = (
    [
        "sudo",
        "-n",
        "mysql",
        "--protocol=socket",
        "-u",
        "root",
        "-N",
        "-B",
        "-e",
        "SHOW DATABASES",
    ],
    [
        "sudo",
        "-n",
        "mysql",
        "--defaults-file=/etc/mysql/debian.cnf",
        "-N",
        "-B",
        "-e",
        "SHOW DATABASES",
    ],
)


def list_databases(password: Optional[str] = None) -> DBList:
    env = _env_with_pwd(password)
    last_err: Optional[Exception] = None

    for cmd in _ATTEMPTS:
        try:
            out = subprocess.check_output(cmd, env=env, text=True, stderr=subprocess.STDOUT)
            names = [ln.strip() for ln in out.splitlines() if ln.strip()]
            names = [n for n in names if n not in SYSTEM_SCHEMAS]
            names.sort()
            return DBList(names)
        except Exception as exc:  # pragma: no cover - error path
            last_err = exc

    for cmd in _SUDO_ATTEMPTS:
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            names = [ln.strip() for ln in out.splitlines() if ln.strip()]
            names = [n for n in names if n not in SYSTEM_SCHEMAS]
            names.sort()
            return DBList(names)
        except Exception as exc:  # pragma: no cover - error path
            last_err = exc

    raise DBListError(str(last_err) if last_err else "Unknown DB list error")


def cache_root_password(pwd: str) -> None:
    global _CACHED_ROOT_PASSWORD
    _CACHED_ROOT_PASSWORD = pwd

WP_DB_NAME_RE = re.compile(r"define\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
WP_DB_USER_RE = re.compile(r"define\(\s*['\"]DB_USER['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
WP_DB_HOST_RE = re.compile(r"define\(\s*['\"]DB_HOST['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
# Optional: table prefix
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
