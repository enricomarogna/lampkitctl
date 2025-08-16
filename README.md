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
* [APT lock handling](#apt-lock-handling)
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

### Quick installer

```bash
# HTTPS (recommended)
curl -fsSL https://raw.githubusercontent.com/enricomarogna/lampkitctl/<BRANCH>/scripts/install-lampkitctl.sh | bash

# Or with sudo up-front (script will still run git/pip as your user):
curl -fsSL https://raw.githubusercontent.com/enricomarogna/lampkitctl/<BRANCH>/scripts/install-lampkitctl.sh | sudo bash
```

**Options:**

* `--branch <name>` – Git branch to checkout (default: `main`)
* `--dir <path>` – Install directory (default: `~/lampkitctl`)
* `--with-tui` – Install optional extras `.[tui]`
* `--no-launcher` – Skip installing `/usr/bin/lampkitctl`
* `--use-ssh` – Clone via SSH instead of HTTPS
* `--wait-apt <sec>` – Wait up to N seconds for apt/dpkg locks (0 to disable)
* `--update-only` – Only update an existing clone

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
sudo apt update
sudo apt install python3.12-venv

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
```

### Global launcher for sudo
If `sudo lampkitctl` is not found, install a global launcher that forwards to your current virtualenv:

```bash
# Run once (will prompt for sudo if needed)
lampkitctl install-launcher

# Now these work:
sudo lampkitctl menu
sudo lampkitctl install-lamp
```

If you move or delete the virtualenv, recreate the launcher:

```bash
lampkitctl uninstall-launcher
lampkitctl install-launcher
```

Alternatively, run without sudo and the tool will auto-elevate when required.

Legacy: `python main.py --help` also works.

---

## Quick Start

Commands run preflight checks and provide guidance if the environment is
missing pieces. Informational output is color-coded: errors appear in **red**,
warnings in **yellow**, and successes in **green**.

### Launch the interactive menu

```bash
lampkitctl install-launcher  # run once to enable sudo lampkitctl
sudo lampkitctl menu
```

When elevation is required, the tool continues the chosen action after
acquiring sudo; you do not need to re-select options.

Choosing **Create a site** performs a LAMP preflight before asking for
domain or database details. If Apache, MySQL, or PHP are missing, the menu
offers to run `install-lamp` and resumes site creation once the installation
completes.

### Install the LAMP stack

```bash
sudo lampkitctl install-lamp --db-engine auto
sudo lampkitctl install-lamp --db-engine mysql
sudo lampkitctl install-lamp --db-engine mariadb
# or simulate without changes:
sudo lampkitctl install-lamp --db-engine auto --dry-run
```

By default the installer prompts to set a **database root password**. For a
non-interactive run supply the password via environment variable:

```bash
# interactive
sudo "$(command -v lampkitctl)" install-lamp --db-engine auto

# non-interactive
export LAMPKITCTL_DB_ROOT_PASS='S3cure,Long,Unique!'
sudo "$(command -v lampkitctl)" install-lamp --db-engine auto \
     --db-root-pass-env LAMPKITCTL_DB_ROOT_PASS \
     --db-root-plugin caching_sha2_password  # MySQL only, optional
```

> With MariaDB the installer switches root from socket-only to password
> authentication.

> **Note:** The install will abort if another apt/dpkg process holds the lock.
> Wait for it to finish or close other package managers.

### Database engine detection

`install-lamp` refreshes the apt cache and picks `mysql-server` when available,
falling back to `mariadb-server`. Override the choice with `--db-engine mysql`
or `--db-engine mariadb`.

### Troubleshooting

- **Package not found** – run `sudo apt-get update`, ensure your Ubuntu release
  is supported, or try `--db-engine mariadb` if MySQL packages are missing.
- **APT lock** – another package manager is running. Wait or close apt/dpkg
  processes. Inspect with `ps aux | egrep 'apt|dpkg'`.

### Create a site

```bash
sudo "$(command -v lampkitctl)" create-site example.local \
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

## APT lock handling

APT and dpkg use lock files to prevent concurrent package operations. Services
like `unattended-upgrades` or `apt-daily` may briefly hold these locks. When a
lockfile is present, package installs will fail until it clears.

Commands such as `install-lamp` accept ``--wait-apt-lock`` to automatically wait
for the lock. The default is ``120`` seconds; use ``0`` to disable waiting.

```bash
sudo lampkitctl install-lamp --wait-apt-lock 180
Waiting for apt lock held by PID 915 (unattended-upgr) on /var/lib/dpkg/lock-frontend ... 27/180s
```

Inspect locks manually with:

```bash
ps -eo pid,comm | grep unattended
lslocks -o PID,COMMAND,PATH | grep lock
lsof -Fpcn /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock
```

---

## CLI Reference

> Exact command names/options may vary slightly by version. Run `lampkitctl --help` for the current details.
> Install the launcher via `lampkitctl install-launcher` to run commands with `sudo lampkitctl`.
> Without it, prefix commands with `sudo "$(command -v lampkitctl)"`.

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
* `--db-root-auth {auto,password,socket}`
* `--db-root-pass <password>`


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

**I see red or yellow messages**
Colored output highlights problems (red) or warnings (yellow). Use the provided
guidance to resolve issues before re-running commands.

**`sudo lampkitctl` returns "command not found"**
Some systems configure `sudo` with a *secure* `PATH` that omits your virtualenv. Install the global launcher so `sudo` can find the CLI:

```bash
lampkitctl install-launcher
```

Alternatively, run commands without sudo and the tool will auto-elevate, or invoke via `sudo "$(command -v lampkitctl)" …`.

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
