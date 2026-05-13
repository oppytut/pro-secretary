#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/ai-secretary}"
WORKFLOW_DIR="${WORKFLOW_DIR:-${DEPLOY_PATH}/n8n/workflows}"

if [[ ! -d "${WORKFLOW_DIR}" ]]; then
    echo "workflow dir not found: ${WORKFLOW_DIR}" >&2
    exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -qx n8n; then
    echo "n8n container not running" >&2
    exit 1
fi

echo "copying workflows into n8n container"
docker exec n8n mkdir -p /tmp/workflows-import
for f in "${WORKFLOW_DIR}"/*.json; do
    docker cp "$f" "n8n:/tmp/workflows-import/$(basename "$f")"
done

echo "importing"
docker exec n8n n8n import:workflow --separate --input=/tmp/workflows-import

echo "activating all imported workflows"
docker exec n8n sh -c 'n8n list:workflow | tail -n +2 | while IFS= read -r line; do
  id=$(printf "%s" "$line" | cut -d"|" -f1)
  [ -n "$id" ] && n8n update:workflow --id="$id" --active=true
done'

echo "done. listing:"
docker exec n8n n8n list:workflow
