#!/bin/bash
set -euo pipefail

export TZ="${TZ:-Asia/Jakarta}"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/ai-secretary}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALLOWED_USERS="${TELEGRAM_ALLOWED_USERS:-}"
BACKUP_PASSPHRASE_FILE="${BACKUP_PASSPHRASE_FILE:-/root/.backup-passphrase}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/ai-secretary}"

SANDBOX="$(mktemp -d -t verify-backup-XXXXXX)"
trap 'rm -rf "$SANDBOX"' EXIT

ERRORS=()
DETAILS=()

note_ok() { DETAILS+=("✓ $1"); }
note_err() { ERRORS+=("✗ $1"); DETAILS+=("✗ $1"); }

LATEST=$(ls -t "$BACKUP_DIR"/*.tar.gz "$BACKUP_DIR"/*.tar.gz.gpg 2>/dev/null | head -1 || true)
if [ -z "$LATEST" ]; then
    note_err "No backup archive found in $BACKUP_DIR"
    SUMMARY="❌ Backup verify FAILED — no archives in $BACKUP_DIR"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
            -d text="$SUMMARY" > /dev/null 2>&1 || true
    fi
    exit 1
fi

echo "[$(date)] Verifying: $LATEST"
ARCHIVE_NAME="$(basename "$LATEST")"
ARCHIVE_AGE_HOURS=$(( ( $(date +%s) - $(stat -c %Y "$LATEST") ) / 3600 ))

cd "$SANDBOX"
if [[ "$LATEST" == *.gpg ]]; then
    if [ ! -f "$BACKUP_PASSPHRASE_FILE" ]; then
        note_err "Encrypted archive but passphrase file missing"
    else
        gpg --batch --decrypt --passphrase-file "$BACKUP_PASSPHRASE_FILE" "$LATEST" 2>/dev/null | tar -xzf - || note_err "Decrypt + extract failed"
    fi
else
    tar -xzf "$LATEST" || note_err "Extract failed"
fi

INNER=$(ls -d 20[0-9][0-9]-* 2>/dev/null | head -1 || true)
if [ -z "$INNER" ]; then
    note_err "Archive missing expected inner dated dir"
else
    cd "$INNER"

    if [ -f n8n-workflows.json ]; then
        WF_COUNT=$(python3 -c "import json,sys; d=json.load(open('n8n-workflows.json')); print(len(d) if isinstance(d, list) else 0)" 2>/dev/null || echo "ERR")
        if [[ "$WF_COUNT" =~ ^[0-9]+$ ]] && [ "$WF_COUNT" -gt 0 ]; then
            note_ok "n8n workflows JSON valid ($WF_COUNT workflows)"
        else
            note_err "n8n-workflows.json invalid or empty"
        fi
    else
        note_err "n8n-workflows.json missing"
    fi

    if [ -f n8n-data.tar.gz ]; then
        mkdir -p _n8n
        if tar -xzf n8n-data.tar.gz -C _n8n 2>/dev/null; then
            DB="_n8n/data/database.sqlite"
            if [ -f "$DB" ]; then
                INTEGRITY=$(sqlite3 "$DB" 'PRAGMA integrity_check;' 2>/dev/null || echo "FAIL")
                if [ "$INTEGRITY" = "ok" ]; then
                    DB_WF=$(sqlite3 "$DB" 'SELECT COUNT(*) FROM workflow_entity;' 2>/dev/null || echo 0)
                    note_ok "n8n SQLite integrity ok ($DB_WF workflow rows)"
                else
                    note_err "n8n SQLite integrity check FAILED: $INTEGRITY"
                fi
            else
                note_err "n8n-data missing database.sqlite"
            fi
        else
            note_err "n8n-data.tar.gz extract failed"
        fi
    else
        note_err "n8n-data.tar.gz missing"
    fi

    if [ -f obsidian-vault.tar.gz ]; then
        MD_COUNT=$(tar -tzf obsidian-vault.tar.gz | grep -c '\.md$' || true)
        if [ "$MD_COUNT" -gt 0 ]; then
            note_ok "vault tarball OK ($MD_COUNT markdown files)"
        else
            note_err "vault tarball has 0 markdown files"
        fi
    else
        note_err "obsidian-vault.tar.gz missing"
    fi

    if [ -f configs.tar.gz ]; then
        mkdir -p _cfg
        if tar -xzf configs.tar.gz -C _cfg 2>/dev/null; then
            ENV_FILE="_cfg/.env"
            COMPOSE_FILE="_cfg/docker-compose.yml"
            MISSING_KEYS=""
            if [ -f "$ENV_FILE" ]; then
                for KEY in AGENT_SECRET DATABASE_URL QDRANT_URL TELEGRAM_BOT_TOKEN; do
                    if ! grep -q "^${KEY}=." "$ENV_FILE"; then
                        MISSING_KEYS="$MISSING_KEYS $KEY"
                    fi
                done
                if [ -n "$MISSING_KEYS" ]; then
                    note_err "configs .env missing keys:$MISSING_KEYS"
                else
                    note_ok ".env has 4 critical secrets"
                fi
            else
                note_err "configs missing .env"
            fi

            if [ -f "$COMPOSE_FILE" ]; then
                if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config --quiet 2>/dev/null; then
                    note_ok "docker-compose.yml validates"
                else
                    note_err "docker-compose.yml invalid"
                fi
            else
                note_err "configs missing docker-compose.yml"
            fi
        else
            note_err "configs.tar.gz extract failed"
        fi
    else
        note_err "configs.tar.gz missing"
    fi
fi

if [ "${#ERRORS[@]}" -eq 0 ]; then
    SUMMARY="✅ Backup verify PASS: $ARCHIVE_NAME (age ${ARCHIVE_AGE_HOURS}h)"
    EXIT=0
else
    SUMMARY="❌ Backup verify FAIL: $ARCHIVE_NAME (age ${ARCHIVE_AGE_HOURS}h, ${#ERRORS[@]} error)"
    EXIT=1
fi

REPORT="$SUMMARY"$'\n'
for d in "${DETAILS[@]}"; do
    REPORT+="$d"$'\n'
done

echo "$REPORT"

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
        --data-urlencode "text=$REPORT" > /dev/null 2>&1 || true
fi

exit $EXIT
