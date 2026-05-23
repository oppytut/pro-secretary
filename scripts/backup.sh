#!/bin/bash
set -euo pipefail

export TZ="${TZ:-Asia/Jakarta}"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/ai-secretary}"
DATE=$(date +%Y-%m-%d_%H%M)
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALLOWED_USERS="${TELEGRAM_ALLOWED_USERS:-}"
QDRANT_URL="${QDRANT_URL:-}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/ai-secretary}"
OBSIDIAN_VAULT_PATH="${OBSIDIAN_VAULT_PATH:-${DEPLOY_PATH}/vault}"
BACKUP_PASSPHRASE_FILE="${BACKUP_PASSPHRASE_FILE:-/root/.backup-passphrase}"

notify_failure() {
    local exit_code=$?
    local line_no=$1
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
            -d text="❌ Backup FAILED at line ${line_no} (exit ${exit_code}). Check /var/log/backup.log" > /dev/null 2>&1 || true
    fi
}
trap 'notify_failure $LINENO' ERR

mkdir -p "$BACKUP_DIR/$DATE"

echo "[$(date)] Starting backup: $DATE"

echo "  [1/5] n8n workflows + data..."
docker exec n8n n8n export:workflow --all --output=/tmp/workflows.json 2>/dev/null || true
docker cp n8n:/tmp/workflows.json "$BACKUP_DIR/$DATE/n8n-workflows.json" 2>/dev/null || true
docker run --rm -v ai-secretary_n8n_data:/data -v "$BACKUP_DIR/$DATE":/backup alpine \
    tar czf /backup/n8n-data.tar.gz /data 2>/dev/null || \
    docker run --rm -v n8n_data:/data -v "$BACKUP_DIR/$DATE":/backup alpine \
    tar czf /backup/n8n-data.tar.gz /data 2>/dev/null || true

echo "  [2/5] Qdrant Cloud snapshots..."
if [ -n "$QDRANT_URL" ] && [ -n "$QDRANT_API_KEY" ]; then
    for collection in knowledge agent_memory tasks people decisions code_chunks; do
        curl -s -X POST "${QDRANT_URL}/collections/$collection/snapshots" \
            -H "api-key: $QDRANT_API_KEY" > /dev/null 2>&1 || true
    done
fi

echo "  [3/5] Obsidian vault..."
if [ -d "$OBSIDIAN_VAULT_PATH" ]; then
    tar czf "$BACKUP_DIR/$DATE/obsidian-vault.tar.gz" -C "$(dirname "$OBSIDIAN_VAULT_PATH")" \
        "$(basename "$OBSIDIAN_VAULT_PATH")" 2>/dev/null || true
fi

echo "  [4/5] Configs (compose + env + app code + systemd unit)..."
tar czf "$BACKUP_DIR/$DATE/configs.tar.gz" \
    -C "$DEPLOY_PATH" \
    docker-compose.yml .env \
    caddy/ telegram-bot/ langgraph-agent/ systemd/ scripts/ 2>/dev/null || true

echo "  [5/5] Sealing archive..."
if [ -f "$BACKUP_PASSPHRASE_FILE" ]; then
    tar czf - -C "$BACKUP_DIR" "$DATE" | gpg --batch --symmetric --cipher-algo AES256 \
        --passphrase-file "$BACKUP_PASSPHRASE_FILE" \
        -o "$BACKUP_DIR/$DATE.tar.gz.gpg"
    rm -rf "$BACKUP_DIR/$DATE"
    BACKUP_FILE="$BACKUP_DIR/$DATE.tar.gz.gpg"
else
    tar czf "$BACKUP_DIR/$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
    rm -rf "$BACKUP_DIR/$DATE"
    BACKUP_FILE="$BACKUP_DIR/$DATE.tar.gz"
fi

find "$BACKUP_DIR" -maxdepth 1 -name "*.tar.gz*" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

R2_UPLOADED=""
if [ -n "${R2_ACCESS_KEY_ID:-}" ] && [ -n "${R2_SECRET_ACCESS_KEY:-}" ] && [ -n "${R2_ENDPOINT:-}" ] && [ -n "${R2_BUCKET:-}" ]; then
    if command -v aws >/dev/null 2>&1; then
        R2_KEY="backups/$(basename "$BACKUP_FILE")"
        if AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
           AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
           aws s3 cp "$BACKUP_FILE" "s3://${R2_BUCKET}/${R2_KEY}" \
              --endpoint-url "$R2_ENDPOINT" \
              --no-progress 2>&1 | tail -3; then
            R2_UPLOADED=" → R2:${R2_BUCKET}/${R2_KEY}"
            echo "[$(date)] Uploaded to R2: ${R2_BUCKET}/${R2_KEY}"
        else
            echo "[$(date)] R2 upload failed (non-fatal)"
        fi
    else
        echo "[$(date)] aws CLI not installed, skipping R2 upload"
    fi
fi

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
        -d text="✅ Backup $DATE ($BACKUP_SIZE)${R2_UPLOADED}" > /dev/null 2>&1
fi
