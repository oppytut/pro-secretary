#!/bin/bash
set -euo pipefail

export TZ="${TZ:-Asia/Jakarta}"

ARCHIVE="${1:-}"
TARGET="${2:-}"
BACKUP_PASSPHRASE_FILE="${BACKUP_PASSPHRASE_FILE:-/root/.backup-passphrase}"

usage() {
    cat <<EOF
Usage: $0 <archive> [target-dir]

  archive     Path to backup file (.tar.gz or .tar.gz.gpg)
              May be local path, or s3://bucket/key for R2 download
  target-dir  Where to extract (default: /tmp/restore-<date>)

Examples:
  $0 /var/backups/ai-secretary/2026-05-15_0954.tar.gz
  $0 /var/backups/ai-secretary/2026-05-15_0954.tar.gz.gpg /tmp/myrestore
  $0 s3://secretary-files/backups/2026-05-15_0954.tar.gz

After extraction, this script INSPECTS the archive and prints suggested
docker/sqlite commands to restore each component. It does NOT auto-apply
to live services.

Verified components (from 2026-05-15 restore drill):
  1. n8n-workflows.json       - re-import via 'docker exec n8n n8n import:workflow'
  2. n8n-data.tar.gz          - replace ai-secretary_n8n_data volume contents
  3. obsidian-vault.tar.gz    - extract to vault/ then 'curl /api/sync_vault'
  4. configs.tar.gz           - manual review before overwriting live .env
  5. Qdrant Cloud snapshots   - hosted, not in archive (provider managed)
EOF
    exit 1
}

[ -z "$ARCHIVE" ] && usage

TARGET="${TARGET:-/tmp/restore-$(date +%Y%m%d_%H%M)}"
mkdir -p "$TARGET"
cd "$TARGET"

if [[ "$ARCHIVE" == s3://* ]]; then
    echo "[1/3] Downloading from R2: $ARCHIVE"
    LOCAL=$(basename "$ARCHIVE")
    AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID:?R2 env not set}" \
    AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY:?R2 env not set}" \
    aws s3 cp "$ARCHIVE" "./$LOCAL" --endpoint-url "${R2_ENDPOINT:?R2 env not set}"
    ARCHIVE="$TARGET/$LOCAL"
fi

[ ! -f "$ARCHIVE" ] && { echo "ERROR: archive not found: $ARCHIVE"; exit 1; }

echo "[2/3] Extracting to $TARGET"
if [[ "$ARCHIVE" == *.gpg ]]; then
    [ ! -f "$BACKUP_PASSPHRASE_FILE" ] && { echo "ERROR: encrypted archive but no passphrase file at $BACKUP_PASSPHRASE_FILE"; exit 1; }
    gpg --batch --decrypt --passphrase-file "$BACKUP_PASSPHRASE_FILE" "$ARCHIVE" | tar -xzf -
else
    tar -xzf "$ARCHIVE"
fi

INNER=$(ls -d 2026-* 2>/dev/null | head -1)
[ -z "$INNER" ] && { echo "ERROR: archive does not contain expected inner dir"; exit 1; }
cd "$INNER"

echo "[3/3] Inspecting components in $TARGET/$INNER"
echo

echo "========================================"
echo "n8n-workflows.json"
echo "========================================"
if [ -f n8n-workflows.json ]; then
    python3 -c "
import json
d = json.load(open('n8n-workflows.json'))
print(f'  workflows: {len(d)}')
for w in d:
    print(f'    - {w[\"name\"]} (active: {w.get(\"active\")}, nodes: {len(w.get(\"nodes\", []))})')
"
    echo
    echo "  RESTORE: copy into n8n container then import:"
    echo "    docker cp n8n-workflows.json n8n:/tmp/import.json"
    echo "    docker exec n8n n8n import:workflow --input=/tmp/import.json"
else
    echo "  MISSING"
fi
echo

echo "========================================"
echo "n8n-data.tar.gz (SQLite + storage)"
echo "========================================"
if [ -f n8n-data.tar.gz ]; then
    echo "  size: $(du -h n8n-data.tar.gz | cut -f1)"
    echo "  entries: $(tar -tzf n8n-data.tar.gz | wc -l)"
    echo
    echo "  RESTORE (DESTRUCTIVE - overwrites live n8n_data volume):"
    echo "    docker compose stop n8n"
    echo "    docker run --rm -v ai-secretary_n8n_data:/data -v \$PWD:/backup alpine \\"
    echo "      sh -c 'rm -rf /data/* && tar -xzf /backup/n8n-data.tar.gz -C / --strip-components=0'"
    echo "    docker compose start n8n"
else
    echo "  MISSING"
fi
echo

echo "========================================"
echo "obsidian-vault.tar.gz"
echo "========================================"
if [ -f obsidian-vault.tar.gz ]; then
    echo "  files: $(tar -tzf obsidian-vault.tar.gz | grep -c '\.md$') markdown"
    echo "  total entries: $(tar -tzf obsidian-vault.tar.gz | wc -l)"
    echo
    echo "  RESTORE:"
    echo "    DEPLOY_PATH=\${DEPLOY_PATH:-/opt/ai-secretary}"
    echo "    tar -xzf obsidian-vault.tar.gz -C \$DEPLOY_PATH --overwrite"
    echo "    curl -X POST -H \"X-Agent-Secret: \$AGENT_SECRET\" \\"
    echo "         http://localhost:8090/api/sync_vault    # via container exec from host"
else
    echo "  MISSING"
fi
echo

echo "========================================"
echo "configs.tar.gz"
echo "========================================"
if [ -f configs.tar.gz ]; then
    echo "  entries: $(tar -tzf configs.tar.gz | wc -l)"
    echo "  WARNING: contains .env with current secrets. Review before overwriting."
    echo
    echo "  INSPECT:"
    echo "    mkdir _configs && tar -xzf configs.tar.gz -C _configs"
    echo "    diff _configs/.env \$DEPLOY_PATH/.env"
    echo "  RESTORE (selective):"
    echo "    cp _configs/.env \$DEPLOY_PATH/.env  # if rotating to backed-up secrets"
    echo "    cp _configs/docker-compose.yml \$DEPLOY_PATH/   # rare; usually pull from git instead"
else
    echo "  MISSING"
fi
echo

echo "========================================"
echo "Qdrant Cloud (NOT in archive)"
echo "========================================"
echo "  Qdrant Cloud manages snapshots provider-side."
echo "  RESTORE via Qdrant Cloud dashboard or API:"
echo "    curl -X POST \"\$QDRANT_URL/collections/<name>/snapshots/recover\" \\"
echo "         -H \"api-key: \$QDRANT_API_KEY\" \\"
echo "         -d '{\"location\": \"<snapshot-url>\"}'"
echo

echo "Inspection complete. Artifacts at: $TARGET/$INNER"
echo "Cleanup when done: rm -rf $TARGET"
