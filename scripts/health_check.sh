#!/bin/bash
set -euo pipefail

SERVICES=(
    "n8n|http://localhost:5678/healthz"
    "calcom|http://localhost:3000/"
    "langgraph-agent|container:langgraph-agent:http://localhost:8090/health"
)

QDRANT_URL="${QDRANT_URL:-}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALLOWED_USERS="${TELEGRAM_ALLOWED_USERS:-}"
CHECK_TUNNEL_SERVICE="${CHECK_TUNNEL_SERVICE:-llm-tunnel.service}"

ALERT=""
CHECKED=0
FAILED=0

check_http() {
    local url="$1"
    curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$url" 2>/dev/null || echo "000"
}

check_container_http() {
    local container="$1" url="$2"
    docker exec "$container" sh -c "curl -s -o /dev/null -w '%{http_code}' --max-time 15 '$url'" 2>/dev/null || echo "000"
}

for service_info in "${SERVICES[@]}"; do
    IFS='|' read -r name target <<< "$service_info"
    CHECKED=$((CHECKED + 1))

    if [[ "$target" == container:* ]]; then
        IFS=':' read -r _ container proto host_port <<< "$target"
        url="${proto}:${host_port}"
        status_code=$(check_container_http "$container" "$url")
    else
        status_code=$(check_http "$target")
    fi

    if [[ "$status_code" -lt 200 || "$status_code" -ge 400 ]]; then
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

if [ -n "$CHECK_TUNNEL_SERVICE" ] && command -v systemctl >/dev/null 2>&1; then
    CHECKED=$((CHECKED + 1))
    if ! systemctl is-active --quiet "$CHECK_TUNNEL_SERVICE" 2>/dev/null; then
        tunnel_state=$(systemctl is-active "$CHECK_TUNNEL_SERVICE" 2>/dev/null || echo "unknown")
        ALERT+="❌ ${CHECK_TUNNEL_SERVICE} is ${tunnel_state}\n"
        FAILED=$((FAILED + 1))
    fi
fi

if [ -n "$ALERT" ]; then
    echo -e "HEALTH CHECK FAILED ($FAILED/$CHECKED):\n$ALERT"

    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
            -d text="⚠️ HEALTH ALERT ($(date '+%H:%M')):
${ALERT}" > /dev/null 2>&1
    fi

    exit 1
else
    echo "OK: $CHECKED/$CHECKED checks passed ($(date '+%Y-%m-%d %H:%M:%S'))"
    exit 0
fi
