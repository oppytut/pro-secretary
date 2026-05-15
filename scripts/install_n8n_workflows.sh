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

if ! command -v jq >/dev/null 2>&1; then
    echo "jq required on host" >&2
    exit 1
fi

EXISTING="$(docker exec n8n n8n list:workflow 2>/dev/null)"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

declare -a IMPORT_NAMES=()

for f in "${WORKFLOW_DIR}"/*.json; do
    name="$(jq -r '.name' "$f")"
    if [[ -z "$name" || "$name" == "null" ]]; then
        echo "skip $f: missing .name" >&2
        continue
    fi

    existing_id="$(printf '%s\n' "$EXISTING" | awk -F'|' -v n="$name" '$2 == n { print $1; exit }')"

    out="${WORK}/$(basename "$f")"
    if [[ -n "$existing_id" ]]; then
        echo "upsert  $name (id=$existing_id)"
        jq --arg id "$existing_id" '.id = $id' "$f" > "$out"
    else
        echo "create  $name (new)"
        jq 'del(.id)' "$f" > "$out"
    fi
    IMPORT_NAMES+=("$name")
done

if [[ ${#IMPORT_NAMES[@]} -eq 0 ]]; then
    echo "no workflows to import"
    exit 0
fi

docker exec n8n rm -rf /tmp/workflows-import
docker exec n8n mkdir -p /tmp/workflows-import
for f in "${WORK}"/*.json; do
    docker cp "$f" "n8n:/tmp/workflows-import/$(basename "$f")"
done

echo
echo "importing ${#IMPORT_NAMES[@]} workflow(s)"
docker exec n8n n8n import:workflow --separate --input=/tmp/workflows-import

echo
echo "activating imported workflows by name"
POST_IMPORT="$(docker exec n8n n8n list:workflow 2>/dev/null)"
ACTIVATED_ANY=0
for name in "${IMPORT_NAMES[@]}"; do
    id="$(printf '%s\n' "$POST_IMPORT" | awk -F'|' -v n="$name" '$2 == n { print $1; exit }')"
    if [[ -z "$id" ]]; then
        echo "WARN: imported '$name' but cannot resolve id" >&2
        continue
    fi
    echo "activate $name (id=$id)"
    docker exec n8n n8n update:workflow --id="$id" --active=true
    ACTIVATED_ANY=1
done

# n8n 1.x writes active=true to DB but does NOT hot-reload schedule triggers
# in the running process. Without restart, cron-based workflows will silently
# skip their next fire window. Restart is required after activation.
# See TASK.md 2026-05-16 entry for the silent-fail incident this prevents.
if [[ "${ACTIVATED_ANY}" -eq 1 ]]; then
    echo
    echo "restarting n8n to register schedule triggers in running process"
    docker restart n8n >/dev/null
    for i in 1 2 3 4 5 6 7 8 9 10; do
        if docker exec n8n wget -qO- http://localhost:5678/healthz 2>/dev/null | grep -q '"status":"ok"'; then
            echo "n8n healthy after restart (attempt $i)"
            break
        fi
        sleep 3
    done
fi

echo
echo "active workflows now:"
docker exec n8n n8n list:workflow --active=true
