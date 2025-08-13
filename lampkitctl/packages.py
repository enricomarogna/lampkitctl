from __future__ import annotations
import subprocess
from dataclasses import dataclass


@dataclass
class Engine:
    name: str
    server_pkg: str
    client_pkg: str
    service_name: str


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
    return "Candidate:" in out and "(none)" not in out


def detect_db_engine(preferred: str | None = None) -> Engine:
    """Detect a suitable database engine package."""
    if preferred in {"mysql", "mariadb"}:
        if preferred == "mysql" and apt_has_package("mysql-server"):
            return Engine("mysql", "mysql-server", "mysql-client", "mysql")
        if preferred == "mariadb" and apt_has_package("mariadb-server"):
            return Engine("mariadb", "mariadb-server", "mariadb-client", "mariadb")
        # Fall through to auto
    if apt_has_package("mysql-server"):
        return Engine("mysql", "mysql-server", "mysql-client", "mysql")
    if apt_has_package("mariadb-server"):
        return Engine("mariadb", "mariadb-server", "mariadb-client", "mariadb")
    raise SystemExit(
        "No supported DB server package found (mysql-server or mariadb-server). "
        "Run 'apt-get update' or check apt sources."
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
