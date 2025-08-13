# lampkitctl

**lampkitctl** is a **Python CLI** tool that installs and configures a full **LAMP** stack (Linux, Apache, MySQL/MariaDB, PHP) on **Ubuntu-based** systems.
It targets both advanced users—through granular commands—and less experienced users with an upcoming **interactive menu**.

> This project is a Python rewrite and enhancement of the original Bash tool “lamp-mngr.sh”.

---

## Table of Contents

* [Features](#features)
* [Requirements](#requirements)
* [Preflight checks](#preflight-checks)
* [Security & Warnings](#security--warnings)
* [Installation](#installation)
* [Quick Start](#quick-start)
* [CLI Reference](#cli-reference)
* [Project Architecture](#project-architecture)
* [Logging](#logging)
* [Testing & Quality](#testing--quality)
* [Roadmap](#roadmap)
* [Troubleshooting / FAQ](#troubleshooting--faq)
* [Contributing](#contributing)
* [License](#license)
* [Support](#support)
* [Credits](#credits)

---

## Features

* ✅ **LAMP detection & installation**
  Installs Apache, MySQL/MariaDB, PHP (and essential PHP/Apache modules); enables `mod_rewrite`.

* ✅ **Apache VirtualHosts**
  Creates HTTP (and optional SSL) vhosts with dedicated logs and a **DocumentRoot**.

* ✅ **`/etc/hosts` updates**
  Adds `127.0.0.1 <domain>` automatically.

* ✅ **Web root structure**
  Creates site folders under `/var/www/<domain>` with sane permissions.

* ✅ **MySQL/MariaDB provisioning**
  Creates a database + dedicated user with least-privilege grants.

* ✅ **Optional WordPress setup**
  Downloads, extracts, and places WordPress; applies recommended filesystem permissions.

* ✅ **SSL with Certbot (optional)**
  Issues and configures certificates for configured domains.

* ✅ **List & remove sites**
  Lists configured sites; controlled uninstall (with confirmations and optional DB removal).

* ✅ **Dry-run mode**
  Simulates actions **without changing** the system.

* ✅ **Structured logging**
  Clear runtime messages and optional JSON logging for CI/log pipelines.

> **Note:** An **interactive menu (TUI)** will be available as an optional entrypoint (see [Roadmap](#roadmap)).

---

## Requirements

* **OS:** Ubuntu 20.04 / 22.04 / 24.04 (or compatible derivatives).
* **Python:** 3.8+ (3.11+ recommended).
* **Privileges:** many operations require **sudo/root**.
* **Network:** internet access is needed to install packages and (optionally) WordPress.

---

## Preflight checks

Most commands validate that required services and files are present before
running. If something is missing, **lampkitctl** fails fast with an explicit
message and suggested fix. Example:

```
$ lampkitctl --non-interactive create-site example.com --doc-root /var/www/example --db-name db --db-user user --db-password pw
Preflight failed: create-site
- Apache not installed. Run: install-lamp.
- MySQL not installed. Run: install-lamp.
```

For SSL generation:

```
$ lampkitctl --non-interactive generate-ssl example.com
Preflight failed: generate-ssl
- certbot not installed. Run: apt install certbot python3-certbot-apache.
```

Critical prerequisites are **blocking** and abort the command with exit code `2`
without an override prompt (e.g., running `install-lamp` without `sudo`). Use
`--dry-run` to preview actions even when blocking checks fail.

Use these diagnostics to install missing packages or create required files before
retrying.

---

## Security & Warnings

* Some operations are **destructive** (e.g., site/DB removal). The tool asks for confirmation and supports `--dry-run`.
* Secrets are never stored in source; **do not** commit credentials to the repo.
* In production, test changes first in a **VM** or on a **snapshot**.

---

## Installation

### 1) Clone the project

```bash
git clone git@github.com:enricomarogna/lampkitctl.git
cd lampkitctl
```

or via HTTPS:

```bash
git clone https://github.com/enricomarogna/lampkitctl.git
cd lampkitctl
```

### 2) (Recommended) Create a virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

### 3) Install the package

```bash
pip install -e .
# or with optional TUI extras:
pip install -e ".[tui]"
```

### 4) Run

```bash
pip install -e .
lampkitctl --help
# or
python -m lampkitctl --help
```

Legacy: `python main.py --help` also works.

---

## Quick Start

Commands run preflight checks and provide guidance if the environment is
missing pieces.

### Install the LAMP stack

```bash
sudo lampkitctl install-lamp
# or simulate without changes:
sudo lampkitctl install-lamp --dry-run
```

### Create a site

```bash
sudo lampkitctl create-site example.local \
  --doc-root /var/www/example.local \
  --db-name example_db \
  --db-user example_user \
  --db-password 'mypassword' \
  --wordpress
```

> If you omit options, the CLI may prompt for required values.
> Use `--dry-run` to preview actions without changing the system.

### Issue an SSL certificate (Certbot)

```bash
sudo lampkitctl generate-ssl example.local
```

### Set WordPress permissions

```bash
sudo lampkitctl wp-permissions /var/www/example.local
```

### List configured sites

```bash
sudo lampkitctl list-sites
```

### Remove a site

```bash
sudo lampkitctl uninstall-site example.local \
  --doc-root /var/www/example.local \
  --db-name example_db \
  --db-user example_user
```

---

## CLI Reference

> Exact command names/options may vary slightly by version. Run `lampkitctl --help` for the current details.

### Global options

* `--dry-run` — simulate operations without applying changes.
* `--verbose` — increase logging verbosity.
* `--non-interactive` — fail immediately on missing prerequisites.

### Main commands

```bash
install-lamp        # Detect and install Apache, MySQL/MariaDB, PHP and core modules.
create-site         # Create vhost, document root, /etc/hosts entry, DB + user; optional WordPress.
uninstall-site      # Remove vhost, hosts entry, doc root, and drop DB/user.
list-sites          # List sites detected from vhost configuration files.
wp-permissions      # Apply recommended WordPress permissions (owner/group, files/dirs).
generate-ssl        # Issue a certificate with Certbot for a configured domain.
menu                # Launch the interactive menu (if extras installed).
```

**Common options for `create-site`:**

* `--domain <domain>`
* `--doc-root </var/www/domain>`
* `--db-name <name>`
* `--db-user <user>`
* `--db-password <password>`
* `--wordpress`


---

## Project Architecture

Suggested structure (may vary by version):

```text
lampkitctl/
├─ cli.py           # CLI entrypoint (Click/argparse), global flags
├─ system_ops.py    # system commands (apt, systemctl, a2enmod/a2ensite, etc.)
├─ db_ops.py        # DB creation/user/grants, connectivity checks
├─ wp_ops.py        # WordPress download/extract/permissions
├─ utils.py         # helpers (run_cmd, validations, secret masking, etc.)
└─ menu.py          # (roadmap) interactive menu controller (TUI)

tests/
├─ test_cli_*.py
├─ test_system_ops.py
├─ test_db_ops.py
└─ test_wp_ops.py
```

**Principles**

* **Separation of concerns:** isolate system-level operations from orchestration.
* **Mockability:** wrap external commands (`run_cmd`) to simplify testing.
* **Idempotency:** commands strive to be repeatable without unintended side effects.
* **Configurability:** prefer CLI options over complex config files; extensible later.

---

## Logging

* Human-friendly output by default; **verbose** mode for technical detail.
* Optional structured (JSON) logging for integration with log pipelines.
* Credentials are **masked** in logs/output (e.g., `****`).

**Examples:**

```bash
lampkitctl install-lamp --verbose
lampkitctl create-site example.local --doc-root /var/www/example.local --db-name db --db-user user --db-password '****'
```

---

## Testing & Quality

* **Framework:** `pytest`
* **Mocking:** `unittest.mock` for `subprocess.run`, temporary filesystems, and I/O.
* **Coverage:** target ≥ **80%** on modified modules.
* **CI (recommended):** GitHub Actions job that installs dependencies and runs tests.

**Minimal workflow** (`.github/workflows/ci.yml`):

```yaml
name: CI
on:
  push:
  pull_request:
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -U pip
      - run: pip install -r requirements.txt || true
      - run: pip install -r requirements-dev.txt || true
      - run: pip install . || true
      - run: python -m pytest -q
```

---

## Roadmap

* **Interactive menu (TUI):** `lampkitctl menu` with guided selections (InquirerPy/Textual), calling existing logic without duplication.
* **Installation profiles:** presets for dev/stage/prod roles.
* **Optional Nginx integration:** alternative compatibility.
* **Minimal backup/restore:** DB dumps and vhost configuration snapshots.

> Have a feature request? Please open an issue or a PR with a detailed proposal.

---

## Troubleshooting / FAQ

**Do I need sudo?**
Yes—most operations (package install, `/etc` writes, services) require elevated privileges.

**Can I test safely?**
Yes: use `--dry-run` or test in a dedicated VM/container. Quick Docker sandbox:

```bash
docker run -it --rm --name lampkitctl-test ubuntu:22.04 bash
# inside the container:
apt update && apt install -y python3 python3-pip git sudo
git clone https://github.com/enricomarogna/lampkitctl.git
cd lampkitctl
pip install -e .
lampkitctl --help
```

**Is MariaDB supported?**
Yes—DB operations are compatible with MySQL/MariaDB on Ubuntu.

**Is Certbot mandatory?**
No. It’s only needed if you want to issue/manage SSL certificates via `ssl issue`.

---

## Contributing

1. Fork and create a feature branch (e.g., `feat/...`).
2. Follow **PEP8**, add type hints and **Google-style docstrings**.
3. Add/update **tests** and ensure they pass locally (and in CI).
4. Open a **Pull Request** with a clear description (what/why/how to test).

**Guidelines:**

* No secrets in the repo.
* Keep logic testable (wrap system calls).
* Document new CLI options in the README.

---

## License

MIT.

---

## Support Development
If you find this project useful, consider [offering me a beer 🍺](https://www.paypal.com/paypalme/enricomarogna/5) — it helps a lot!

[![Donate via PayPal](https://img.shields.io/badge/PayPal-Buy%20me%20a%20beer-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/enricomarogna/5)

---

## Credits

Author: **Enrico Marogna** – [https://enricomarogna.com](https://enricomarogna.com)

Origin: Python port and extension of the Bash tool “lamp-mngr.sh”.
