#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="llm-tunnel.service"
SERVICE_SRC="$(cd "$(dirname "$0")/.." && pwd)/systemd/${SERVICE_NAME}"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}"

if [[ ! -f "${SERVICE_SRC}" ]]; then
  echo "missing ${SERVICE_SRC}" >&2
  exit 1
fi

if ! command -v autossh >/dev/null 2>&1; then
  echo "installing autossh..."
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -yq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -yq autossh
fi

sudo cp "${SERVICE_SRC}" "${SERVICE_DST}"
sudo chmod 644 "${SERVICE_DST}"
sudo systemctl daemon-reload
sudo systemctl enable --now "${SERVICE_NAME}"

sleep 3
sudo systemctl status "${SERVICE_NAME}" --no-pager | head -10
echo
echo "tunnel listening:"
ss -tlnp 2>/dev/null | grep :20128 || echo "WARN: not listening yet, check: journalctl -u ${SERVICE_NAME} -n 30"
