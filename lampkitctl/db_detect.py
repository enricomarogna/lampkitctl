from __future__ import annotations

import logging
import re
import subprocess
from typing import Literal

logger = logging.getLogger(__name__)


def _dpkg_installed(pkg: str) -> bool:
    """Return True if dpkg reports ``pkg`` as installed."""
    try:
        proc = subprocess.run(
            ["dpkg", "-s", pkg], capture_output=True, text=True
        )
    except OSError:
        return False
    if proc.returncode != 0:
        return False
    return re.search(r"^Status: .* installed", proc.stdout or "", re.MULTILINE) is not None


_ENGINE_NAMES = {"mysql": "mysql-server", "mariadb": "mariadb-server"}


def detect_db_engine() -> Literal["mysql", "mariadb"] | None:
    """Detect the installed database engine.

    Returns ``"mysql"`` or ``"mariadb"`` when one engine is installed, otherwise
    ``None``. Logs the detection source for observability.
    """
    mysql_inst = _dpkg_installed(_ENGINE_NAMES["mysql"])
    mariadb_inst = _dpkg_installed(_ENGINE_NAMES["mariadb"])

    if mysql_inst and not mariadb_inst:
        logger.info("db_engine_autodetect", extra={"engine": "mysql", "source": "dpkg"})
        return "mysql"
    if mariadb_inst and not mysql_inst:
        logger.info("db_engine_autodetect", extra={"engine": "mariadb", "source": "dpkg"})
        return "mariadb"
    if mysql_inst and mariadb_inst:
        logger.info("db_engine_autodetect", extra={"engine": None, "source": "dpkg"})
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
