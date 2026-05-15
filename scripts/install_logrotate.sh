#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/ai-secretary}"
SRC="${DEPLOY_PATH}/ops/logrotate/ai-secretary"
DST="/etc/logrotate.d/ai-secretary"

if [ ! -f "$SRC" ]; then
    echo "missing source: $SRC" >&2
    exit 1
fi

sudo install -m 0644 -o root -g root "$SRC" "$DST"
sudo logrotate --debug "$DST"

echo "installed: $DST"
echo "to force-rotate now (testing): sudo logrotate -fv $DST"
