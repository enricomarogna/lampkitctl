from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import os, re, subprocess

SYSTEM_SCHEMAS = {"information_schema", "mysql", "performance_schema", "sys"}

@dataclass
class DBList:
    databases: list[str]

# Use local socket root by default, avoid echoing creds; allow password via env
# LAMPKITCTL_DB_ROOT_PASS (string) when root requires password.

def _mysql_cmd() -> list[str]:
    return ["mysql", "--protocol=socket", "-u", "root", "-N", "-B"]


def list_databases() -> DBList:
    cmd = _mysql_cmd() + ["-e", "SHOW DATABASES"]
    env = os.environ.copy()
    password = env.get("LAMPKITCTL_DB_ROOT_PASS")
    if password:
        env["MYSQL_PWD"] = password  # avoid -p in argv
    out = subprocess.check_output(cmd, env=env, text=True)
    names = [ln.strip() for ln in out.splitlines() if ln.strip()]
    names = [n for n in names if n not in SYSTEM_SCHEMAS]
    names.sort()
    return DBList(names)

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
