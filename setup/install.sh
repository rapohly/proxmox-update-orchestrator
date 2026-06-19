#!/usr/bin/env bash
set -e

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
sudo $INSTALL python3 python3-venv python3-pip ansible git sshpass
sudo $INSTALL ansible-core

#echo "Setting up venv..."
#python3 -m venv .venv
#source .venv/bin/activate

echo "Installing Python deps..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Done."
