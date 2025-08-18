#!/usr/bin/env bash
# lampkitctl bootstrap installer
# - Clones/updates the repo
# - Creates a venv and installs package (editable), with optional TUI extras
# - Installs a global launcher in /usr/bin so `sudo lampkitctl` works
# Safe to re-run. Uses HTTPS by default to avoid SSH key requirements.

set -Eeuo pipefail

# -----------------------------
# Colors
# -----------------------------
# shellcheck disable=SC2034
if [ -t 1 ]; then
  RED='\033[31m'; YEL='\033[33m'; GRN='\033[32m'; CYN='\033[36m'; MAG='\033[35m'; BLD='\033[1m'; RST='\033[0m'
else
  RED=''; YEL=''; GRN=''; CYN=''; MAG=''; BLD=''; RST=''
fi
note() { printf "%b%s%b\n" "$CYN" "$*" "$RST"; }
warn() { printf "%b%s%b\n" "$YEL" "$*" "$RST"; }
ok()   { printf "%b%s%b\n" "$GRN" "$*" "$RST"; }
err()  { printf "%b%s%b\n" "$RED$BLD" "$*" "$RST"; }

# -----------------------------
# Defaults / args
# -----------------------------
REPO_URL_HTTPS="https://github.com/enricomarogna/lampkitctl.git"
REPO_URL_SSH="git@github.com:enricomarogna/lampkitctl.git"
USE_SSH=0
BRANCH="master"
WITH_TUI=0
INSTALL_LAUNCHER=1
WAIT_APT=120
UPDATE_ONLY=0
DIR_DEFAULT="${HOME}/lampkitctl"
DIR="${DIR_DEFAULT}"

usage() {
  cat <<EOF2
$(basename "$0") [options]
  --branch <name>         Git branch to checkout (default: main)
  --dir <path>            Install directory (default: \$HOME/lampkitctl)
  --with-tui              Install optional extras: .[tui]
  --no-launcher           Do NOT install /usr/bin/lampkitctl
  --use-ssh               Clone via SSH instead of HTTPS
  --wait-apt <sec>        Wait up to N seconds for apt/dpkg locks (default: 120; 0 = no wait)
  --update-only           Do not clone if missing; just pull + reinstall if exists
  -h, --help              Show this help
EOF2
}

while [ "${1:-}" != "" ]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2;;
    --dir) DIR="$2"; shift 2;;
    --with-tui) WITH_TUI=1; shift;;
    --no-launcher) INSTALL_LAUNCHER=0; shift;;
    --use-ssh) USE_SSH=1; shift;;
    --wait-apt) WAIT_APT="$2"; shift 2;;
    --update-only) UPDATE_ONLY=1; shift;;
    -h|--help) usage; exit 0;;
    *) err "Unknown option: $1"; usage; exit 2;;
  esac
done

# -----------------------------
# Detect target user (for sudo runs)
# -----------------------------
TARGET_USER="${SUDO_USER:-${USER:-$(id -un)}}"
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6 || echo "$HOME")
if [ "$DIR" = "$DIR_DEFAULT" ]; then DIR="$TARGET_HOME/lampkitctl"; fi

run_as_target() { sudo -u "$TARGET_USER" -H bash -lc "$*"; }
need_root() { [ "$(id -u)" -eq 0 ] || exec sudo bash "$0" "$@"; }

require_cmd() { command -v "$1" >/dev/null 2>&1 || { err "Missing command: $1"; exit 2; }; }

# -----------------------------
# OS sanity
# -----------------------------
# shellcheck source=/dev/null
if [ -r /etc/os-release ]; then . /etc/os-release; else ID=unknown; VERSION_ID=unknown; fi
note "Detected OS: ${ID:-unknown} ${VERSION_ID:-unknown}"

# -----------------------------
# Wait for apt locks (optional)
# -----------------------------
LOCKS=(/var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock)
is_locked() {
  for p in "${LOCKS[@]}"; do
    if fuser "$p" >/dev/null 2>&1; then return 0; fi
  done
  return 1
}

if [ "${WAIT_APT}" -gt 0 ]; then
  end=$(( $(date +%s) + WAIT_APT ))
  while is_locked; do
    now=$(date +%s)
    [ "$now" -ge "$end" ] && { err "apt/dpkg is busy (timeout ${WAIT_APT}s)."; exit 2; }
    warn "Waiting for apt lock to clear… ($((end-now))s)"
    sleep 3
  done
fi

# -----------------------------
# Ensure prerequisites
# -----------------------------
note "Updating apt index…"
if ! sudo -n true 2>/dev/null; then warn "sudo password may be requested for apt/launcher steps"; fi
sudo apt-get update -y
note "Installing prerequisites (git, python3-venv, python3-pip)…"
sudo apt-get install -y git python3-venv python3-pip >/dev/null

# -----------------------------
# Clone or update
# -----------------------------
REPO_URL="$REPO_URL_HTTPS"; [ "$USE_SSH" -eq 1 ] && REPO_URL="$REPO_URL_SSH"
if [ -d "$DIR/.git" ]; then
  ok "Repository exists → pulling latest on $BRANCH"
  run_as_target "git -C '$DIR' fetch --all --quiet"
  run_as_target "git -C '$DIR' checkout '$BRANCH'"
  run_as_target "git -C '$DIR' pull --ff-only origin '$BRANCH'"
else
  [ "$UPDATE_ONLY" -eq 1 ] && { err "--update-only specified but repo not found at $DIR"; exit 2; }
  note "Cloning $REPO_URL into $DIR (branch $BRANCH)…"
  run_as_target "git clone --branch '$BRANCH' '$REPO_URL' '$DIR'"
fi

# -----------------------------
# Create/upgrade venv & install
# -----------------------------
if [ ! -d "$DIR/.venv" ]; then
  note "Creating virtualenv…"
  run_as_target "python3 -m venv '$DIR/.venv'"
fi
run_as_target "'$DIR/.venv/bin/pip' install -U pip"
run_as_target "cd '$DIR' && '$DIR/.venv/bin/pip' install -e ."
if [ "$WITH_TUI" -eq 1 ]; then
  run_as_target "cd '$DIR' && '$DIR/.venv/bin/pip' install -e '.[tui]'"
fi

# -----------------------------
# Launcher
# -----------------------------
if [ "$INSTALL_LAUNCHER" -eq 1 ]; then
  LAUNCHER=/usr/bin/lampkitctl
  note "Installing global launcher at $LAUNCHER"
  sudo tee "$LAUNCHER" >/dev/null <<LAUNCH
#!/usr/bin/env bash
exec "$DIR/.venv/bin/lampkitctl" "\$@"
LAUNCH
  sudo chmod +x "$LAUNCHER"
fi

# -----------------------------
# Self-test
# -----------------------------
ok "Running self-test…"
run_as_target "'$DIR/.venv/bin/lampkitctl' version || true"
run_as_target "'$DIR/.venv/bin/lampkitctl' --help >/dev/null || true"

if command -v lampkitctl >/dev/null 2>&1; then
  sudo lampkitctl version || true
  sudo lampkitctl --help >/dev/null || true
else
  warn "Global 'lampkitctl' not in PATH yet (no launcher?). You can run: $DIR/.venv/bin/lampkitctl"
fi

ok "Done. Next steps:"
cat <<NEXT
  1) Activate venv (optional):
       source '$DIR/.venv/bin/activate'
  2) Open the menu:
       lampkitctl menu
  3) Or install LAMP directly:
       sudo "\$(command -v lampkitctl)" install-lamp --db-engine auto
NEXT
