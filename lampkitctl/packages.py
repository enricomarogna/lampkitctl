from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Iterable, List

from . import utils


@dataclass
class Engine:
    name: str
    server_pkg: str
    client_pkg: str
    service_name: str


CANDIDATE_RX = re.compile(
    r"^\s*Candidate:\s*(?!\(none\))", re.IGNORECASE | re.MULTILINE
)


def apt_has_package(pkg: str) -> bool:
    """Return ``True`` if ``apt`` reports a candidate for ``pkg``."""

    try:
        p = subprocess.run(
            ["apt-cache", "policy", pkg], capture_output=True, text=True
        )
    except OSError:
        return False
    if p.returncode != 0:
        return False
    out = (p.stdout or "") + (p.stderr or "")
    return bool(CANDIDATE_RX.search(out))


def _candidate_line(pkg: str) -> str:
    try:
        p = subprocess.run(
            ["apt-cache", "policy", pkg], capture_output=True, text=True
        )
    except OSError:
        return "Candidate: (error)"
    out = (p.stdout or "") + (p.stderr or "")
    m = re.search(r"^\s*Candidate:.*$", out, re.MULTILINE)
    return m.group(0).strip() if m else "Candidate: (none)"


def refresh_cache(dry_run: bool = False) -> None:
    utils.run_command(["apt-get", "update"], dry_run=dry_run, capture_output=True)


def is_installed(pkg: str) -> bool:
    """Return ``True`` if ``pkg`` is installed via ``dpkg``."""

    try:
        proc = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", pkg],
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    if proc.returncode != 0:
        return False
    return proc.stdout.strip() == "install ok installed"


def all_installed(pkgs: List[str]) -> bool:
    """Return ``True`` when all packages in ``pkgs`` are installed."""

    return all(is_installed(p) for p in pkgs)


def detect_db_engine(preferred: str | None = None) -> Engine:
    """Detect a suitable database engine package."""

    if preferred == "auto":
        preferred = None
    if preferred == "mysql" and apt_has_package("mysql-server"):
        return Engine("mysql", "mysql-server", "mysql-client", "mysql")
    if preferred == "mariadb" and apt_has_package("mariadb-server"):
        return Engine("mariadb", "mariadb-server", "mariadb-client", "mariadb")

    if apt_has_package("mysql-server"):
        return Engine("mysql", "mysql-server", "mysql-client", "mysql")
    if apt_has_package("mariadb-server"):
        return Engine("mariadb", "mariadb-server", "mariadb-client", "mariadb")
    if apt_has_package("default-mysql-server"):
        return Engine(
            "mysql", "default-mysql-server", "default-mysql-client", "mysql"
        )

    lines = [
        f"mysql-server: {_candidate_line('mysql-server')}",
        f"mariadb-server: {_candidate_line('mariadb-server')}",
        f"default-mysql-server: {_candidate_line('default-mysql-server')}",
    ]
    raise SystemExit(
        "No supported DB server package found\n" + "\n".join(lines)
    )


PHP_BASE = ["php", "libapache2-mod-php", "php-mysql"]
PHP_EXTRAS = [
    "php-curl",
    "php-xml",
    "php-imagick",
    "php-mbstring",
    "php-zip",
    "php-intl",
    "php-gd",
]
APACHE_PKG = "apache2"
CERTBOT_PKGS = ["certbot", "python3-certbot-apache"]


@dataclass(frozen=True)
class PkgStatus:
    """Package state buckets returned by :func:`detect_pkg_status`."""

    missing: List[str]
    upgradable: List[str]
    uptodate: List[str]


_POLICY_RE = re.compile(r"^(Installed|Candidate):\s*(.*)$", re.M)
_DEF_APT_CACHE = ["apt-cache", "policy"]


def _policy(pkg: str) -> tuple[str | None, str | None]:
    """Return (installed, candidate) versions for ``pkg``."""

    out = subprocess.check_output(
        _DEF_APT_CACHE + [pkg], text=True, stderr=subprocess.STDOUT
    )
    inst = cand = None
    for m in _POLICY_RE.finditer(out):
        key, val = m.group(1), m.group(2).strip()
        if key == "Installed":
            inst = val
        elif key == "Candidate":
            cand = val
    return inst, cand


_DEF_NONE = {"(none)", "none", "<none>"}


def detect_pkg_status(pkgs: Iterable[str]) -> PkgStatus:
    """Return package status for ``pkgs``."""

    missing: List[str] = []
    upgradable: List[str] = []
    uptodate: List[str] = []
    for p in pkgs:
        inst, cand = _policy(p)
        if not inst or inst in _DEF_NONE:
            missing.append(p)
        elif cand and cand != inst:
            upgradable.append(p)
        else:
            uptodate.append(p)
    return PkgStatus(missing, upgradable, uptodate)

