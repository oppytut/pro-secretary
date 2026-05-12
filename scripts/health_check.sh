#!/bin/bash
set -euo pipefail

SERVICES=(
    "n8n|http://localhost:5678/healthz"
    "calcom|http://localhost:3000/api/health"
    "openfang|http://localhost:8090/health"
)

QDRANT_URL="${QDRANT_URL:-}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALLOWED_USERS="${TELEGRAM_ALLOWED_USERS:-}"

ALERT=""
CHECKED=0
FAILED=0

for service_info in "${SERVICES[@]}"; do
    IFS='|' read -r name url <<< "$service_info"
    CHECKED=$((CHECKED + 1))

    status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")

    if [ "$status_code" != "200" ]; then
        ALERT+="❌ $name DOWN (HTTP $status_code)\n"
        FAILED=$((FAILED + 1))
    fi
done

if [ -n "$QDRANT_URL" ] && [ -n "$QDRANT_API_KEY" ]; then
    CHECKED=$((CHECKED + 1))
    qdrant_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
        "${QDRANT_URL}/healthz" -H "api-key: ${QDRANT_API_KEY}" 2>/dev/null || echo "000")

    if [ "$qdrant_status" != "200" ]; then
        ALERT+="❌ qdrant-cloud DOWN (HTTP $qdrant_status)\n"
        FAILED=$((FAILED + 1))
    fi
fi

if [ -n "$ALERT" ]; then
    echo -e "HEALTH CHECK FAILED:\n$ALERT"

    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
            -d text="⚠️ HEALTH ALERT ($(date '+%H:%M')):\n${ALERT}" \
            -d parse_mode="HTML" > /dev/null 2>&1
    fi

    exit 1
else
    echo "OK: $CHECKED/$CHECKED services healthy ($(date '+%Y-%m-%d %H:%M:%S'))"
    exit 0
fi
