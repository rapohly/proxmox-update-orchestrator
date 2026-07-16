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

echo "Setting up Ansible directories..."
mkdir -p "$PROJECT_ROOT/ansible/inventories/group_vars/all"

echo "Configuring Ansible vault..."
ansible-vault create "$PROJECT_ROOT/ansible/inventories/group_vars/all/vault.yml"

echo "Configuring runtime directory..."
mkdir "$PROJECT_ROOT/runstate"

echo "Done."