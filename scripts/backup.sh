#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/ai-secretary}"
DATE=$(date +%Y-%m-%d_%H%M)
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALLOWED_USERS="${TELEGRAM_ALLOWED_USERS:-}"
QDRANT_URL="${QDRANT_URL:-}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
OBSIDIAN_VAULT_PATH="${OBSIDIAN_VAULT_PATH:-/opt/ai-secretary/vault}"
BACKUP_PASSPHRASE_FILE="${BACKUP_PASSPHRASE_FILE:-/root/.backup-passphrase}"

mkdir -p "$BACKUP_DIR/$DATE"

echo "[$(date)] Starting backup: $DATE"

echo "  [1/4] Backing up n8n data..."
docker exec n8n n8n export:workflow --all --output=/tmp/workflows.json 2>/dev/null || true
docker cp n8n:/tmp/workflows.json "$BACKUP_DIR/$DATE/n8n-workflows.json" 2>/dev/null || true
docker run --rm -v n8n_data:/data -v "$BACKUP_DIR/$DATE":/backup alpine \
    tar czf /backup/n8n-data.tar.gz /data 2>/dev/null

echo "  [2/4] Triggering Qdrant Cloud snapshots..."
if [ -n "$QDRANT_URL" ] && [ -n "$QDRANT_API_KEY" ]; then
    for collection in knowledge agent_memory tasks people decisions; do
        curl -s -X POST "${QDRANT_URL}/collections/$collection/snapshots" \
            -H "api-key: $QDRANT_API_KEY" > /dev/null 2>&1 || true
    done
fi

echo "  [3/4] Backing up Obsidian vault..."
if [ -d "$OBSIDIAN_VAULT_PATH" ]; then
    tar czf "$BACKUP_DIR/$DATE/obsidian-vault.tar.gz" -C "$(dirname "$OBSIDIAN_VAULT_PATH")" \
        "$(basename "$OBSIDIAN_VAULT_PATH")" 2>/dev/null
fi

echo "  [4/4] Backing up config files..."
tar czf "$BACKUP_DIR/$DATE/configs.tar.gz" \
    docker-compose.yml .env \
    openfang/ caddy/ telegram-bot/ 2>/dev/null || true

if [ -f "$BACKUP_PASSPHRASE_FILE" ]; then
    echo "  Encrypting backup..."
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

find "$BACKUP_DIR" -name "*.tar.gz*" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
        -d text="✅ Backup selesai: $DATE ($BACKUP_SIZE)" > /dev/null 2>&1
fi
