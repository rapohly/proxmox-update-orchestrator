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
    echo "Error: init.py not found."
    exit 1
fi

echo "Installing PUO CLI..."
chmod +x "$PROJECT_ROOT/src/puo.py"
sudo ln -sf "$PROJECT_ROOT/src/puo.py" /usr/local/bin/puo

echo "Verifying PUO CLI..."
if command -v puo >/dev/null 2>&1; then
    echo "PUO CLI installed successfully."
else
    echo "Failed to install PUO CLI."
    exit 1
fi

python3 "$PROJECT_ROOT/src/init.py"