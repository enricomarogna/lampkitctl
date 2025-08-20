from __future__ import annotations

import logging
import re
import subprocess
from typing import Literal

logger = logging.getLogger(__name__)


def _pkg_installed(pkg: str) -> bool:
    """Return ``True`` if ``apt`` reports ``pkg`` as installed."""

    try:
        proc = subprocess.run(
            ["apt-cache", "policy", pkg], capture_output=True, text=True
        )
    except OSError:
        return False
    if proc.returncode != 0:
        return False
    out = proc.stdout or ""
    m = re.search(r"Installed:\s*(.+)", out)
    if not m:
        return False
    ver = m.group(1).strip()
    return ver not in {"(none)", "none", "<none>"}


_ENGINE_NAMES = {"mysql": "mysql-server", "mariadb": "mariadb-server"}


def detect_db_engine() -> Literal["mysql", "mariadb"] | None:
    """Detect the installed database engine.

    Returns ``"mysql"`` or ``"mariadb"`` when one engine is installed, otherwise
    ``None``. Logs the detection source for observability.
    """
    mysql_inst = _pkg_installed(_ENGINE_NAMES["mysql"])
    mariadb_inst = _pkg_installed(_ENGINE_NAMES["mariadb"])

    if mysql_inst and not mariadb_inst:
        logger.info(
            "db_engine_autodetect", extra={"engine": "mysql", "source": "dpkg"}
        )
        return "mysql"
    if mariadb_inst and not mysql_inst:
        logger.info(
            "db_engine_autodetect", extra={"engine": "mariadb", "source": "dpkg"}
        )
        return "mariadb"
    if mysql_inst and mariadb_inst:
        logger.info(
            "db_engine_autodetect", extra={"engine": None, "source": "dpkg"}
        )
        return None

    try:
        proc = subprocess.run(
            ["mysql", "--version"], capture_output=True, text=True
        )
    except OSError:
        logger.info("db_engine_autodetect", extra={"engine": None, "source": "none"})
        return None

    if proc.returncode != 0:
        logger.info("db_engine_autodetect", extra={"engine": None, "source": "none"})
        return None

    out = (proc.stdout or "").lower()
    if "mariadb" in out:
        logger.info("db_engine_autodetect", extra={"engine": "mariadb", "source": "version"})
        return "mariadb"
    if "mysql" in out:
        logger.info("db_engine_autodetect", extra={"engine": "mysql", "source": "version"})
        return "mysql"
    logger.info("db_engine_autodetect", extra={"engine": None, "source": "none"})
    return None
