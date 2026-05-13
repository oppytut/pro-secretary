#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/ai-secretary}"
LOG_DIR="${LOG_DIR:-/var/log}"

HEALTH="*/5 * * * * set -a; . ${DEPLOY_PATH}/.env; set +a; ${DEPLOY_PATH}/scripts/health_check.sh >> ${LOG_DIR}/health-check.log 2>&1"
BACKUP="30 2 * * *  set -a; . ${DEPLOY_PATH}/.env; set +a; ${DEPLOY_PATH}/scripts/backup.sh >> ${LOG_DIR}/backup.log 2>&1"
SYNC="*/30 * * * * set -a; . ${DEPLOY_PATH}/.env; set +a; AGENT_URL=container ${DEPLOY_PATH}/scripts/trigger_sync_vault.sh >> ${LOG_DIR}/vault-sync.log 2>&1"

for f in health-check.log backup.log vault-sync.log; do
    sudo touch "${LOG_DIR}/$f"
    sudo chown "$USER":"$USER" "${LOG_DIR}/$f"
done

CURRENT=$(crontab -l 2>/dev/null | grep -Ev 'health_check\.sh|backup\.sh|trigger_sync_vault\.sh' || true)

{
    printf '%s\n' "$CURRENT"
    printf '%s\n' "$HEALTH"
    printf '%s\n' "$BACKUP"
    printf '%s\n' "$SYNC"
} | crontab -

echo "installed cron:"
crontab -l
