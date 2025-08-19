from __future__ import annotations
from dataclasses import dataclass
import glob
import os
import re
from typing import List


@dataclass
class VHost:
    domain: str
    docroot: str | None
    conf_path: str
    ssl: bool


_SERVER_NAME_RE = re.compile(r"^\s*ServerName\s+(?P<name>\S+)", re.IGNORECASE)
_DOCROOT_RE = re.compile(r"^\s*DocumentRoot\s+(?P<path>\S+)", re.IGNORECASE)
_SSL_REWRITE_RE = re.compile(r"https?://", re.IGNORECASE)


def list_vhosts(conf_dir: str = "/etc/apache2/sites-available") -> List[VHost]:
    vhosts: dict[str, VHost] = {}
    for path in sorted(glob.glob(os.path.join(conf_dir, "*.conf"))):
        domain: str | None = None
        docroot: str | None = None
        ssl = False
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if domain is None:
                        m = _SERVER_NAME_RE.match(line)
                        if m:
                            domain = m.group("name").strip()
                    if docroot is None:
                        m = _DOCROOT_RE.match(line)
                        if m:
                            docroot = m.group("path").strip()
                    if not ssl and _SSL_REWRITE_RE.search(line):
                        ssl = True
        except Exception:
            continue
        if domain and domain not in vhosts:
            vhosts[domain] = VHost(domain, docroot, path, ssl)
    return list(vhosts.values())
