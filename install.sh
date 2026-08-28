#!/usr/bin/env bash
set -euo pipefail

# NetHealth Community - one-line installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/install.sh | sudo bash -s -- https://github.com/OWNER/REPO.git

REPO_URL="${1:-}"
INSTALL_DIR="${NETHEALTH_INSTALL_DIR:-/opt/nethealth-community}"

if [[ -z "$REPO_URL" ]]; then
  echo "Usage: curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/install.sh | sudo bash -s -- https://github.com/OWNER/REPO.git"
  exit 2
fi

if [[ $EUID -ne 0 ]]; then
  echo "Please run the installer with sudo/root."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y ca-certificates curl git openssl

if ! command -v docker >/dev/null 2>&1; then
  echo "Installing Docker Engine..."
  curl -fsSL https://get.docker.com | sh
fi

systemctl enable --now docker

# Docker Compose V2 is included as a plugin on modern Docker installations.
if ! docker compose version >/dev/null 2>&1; then
  apt-get install -y docker-compose-plugin || true
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose V2 is required but was not found."
  exit 1
fi

mkdir -p "$INSTALL_DIR"
if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" fetch --all --prune
  git -C "$INSTALL_DIR" reset --hard origin/main
else
  rm -rf "$INSTALL_DIR"
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

# Generate production-safe secrets on first install.
if grep -q '^POSTGRES_PASSWORD=change-me' .env || grep -q '^POSTGRES_PASSWORD=$' .env; then
  sed -i "s#^POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=$(openssl rand -hex 24)#" .env
fi
if grep -q '^JWT_SECRET=change-me' .env || grep -q '^JWT_SECRET=$' .env; then
  sed -i "s#^JWT_SECRET=.*#JWT_SECRET=$(openssl rand -hex 48)#" .env
fi

mkdir -p backups
touch backups/.keep
chmod 700 backups || true

# Optional: create a stable local name in /etc/hosts for convenience.
SERVER_IP=$(hostname -I | awk '{print $1}')

# Start the stack.
docker compose up -d --build

sleep 5

echo
echo "=============================================="
echo " NetHealth Community installed successfully"
echo "=============================================="
echo "Server IP : ${SERVER_IP:-YOUR_SERVER_IP}"
echo "Web panel : http://${SERVER_IP:-YOUR_SERVER_IP}"
echo "Install  : ${INSTALL_DIR}"
echo
echo "First login: create the administrator account in the web panel."
echo "Logs: cd ${INSTALL_DIR} && docker compose logs -f"
