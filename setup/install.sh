#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Detecting package manager..."

if command -v apt >/dev/null 2>&1; then
    PM="apt"
    UPDATE="apt update"
    INSTALL="apt install -y"
elif command -v dnf >/dev/null 2>&1; then
    PM="dnf"
    UPDATE="dnf check-update || true"
    INSTALL="dnf install -y"
else
    echo "Unsupported system"
    exit 1
fi

echo "Updating packages..."
sudo $UPDATE

echo "Installing dependencies..."
sudo $INSTALL python3 ansible-core

if [[ ! -f "$PROJECT_ROOT/src/init.py" ]]; then
    echo "Error: parse_remotes.py not found."
    exit 1
fi

python3 "$PROJECT_ROOT/src/init.py"