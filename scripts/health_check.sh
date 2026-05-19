#!/bin/bash
set -euo pipefail

export TZ="${TZ:-Asia/Jakarta}"

SERVICES=(
    "n8n|container:n8n:http://localhost:5678/healthz"
    "calcom|container:calcom:http://localhost:3000/"
    "langgraph-agent|container:langgraph-agent:http://localhost:8090/health"
)

QDRANT_URL="${QDRANT_URL:-}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALLOWED_USERS="${TELEGRAM_ALLOWED_USERS:-}"
CHECK_TUNNEL_SERVICE="${CHECK_TUNNEL_SERVICE:-llm-tunnel.service}"
GRACE_SECONDS="${HEALTH_GRACE_SECONDS:-60}"
STATE_FILE="${HEALTH_STATE_FILE:-/var/lib/ai-secretary/health-state}"

mkdir -p "$(dirname "$STATE_FILE")" 2>/dev/null || true

ALERT=""
CHECKED=0
FAILED=0
SKIPPED=""

check_http() {
    local url="$1"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$url" 2>/dev/null)
    [[ -z "$code" ]] && code="000"
    echo "$code"
}

check_container_http() {
    local container="$1" url="$2"
    local code
    code=$(docker exec "$container" sh -c "
        if command -v curl >/dev/null 2>&1; then
            curl -s -o /dev/null -w '%{http_code}' --max-time 15 '$url'
        elif command -v wget >/dev/null 2>&1; then
            wget -qO- --server-response --timeout=15 '$url' 2>&1 | awk '/^  HTTP/{c=\$2} END{print c}'
        else
            echo 000
        fi
    " 2>/dev/null)
    [[ -z "$code" ]] && code="000"
    echo "$code"
}

container_age_seconds() {
    local container="$1"
    local started
    started=$(docker inspect "$container" --format "{{.State.StartedAt}}" 2>/dev/null) || return 1
    [[ -z "$started" ]] && return 1
    local started_epoch
    started_epoch=$(date -d "$started" +%s 2>/dev/null) || return 1
    local now_epoch
    now_epoch=$(date +%s)
    echo $(( now_epoch - started_epoch ))
}

for service_info in "${SERVICES[@]}"; do
    IFS='|' read -r name target <<< "$service_info"
    CHECKED=$((CHECKED + 1))

    if [[ "$target" == container:* ]]; then
        IFS=':' read -r _ container proto host_port <<< "$target"
        url="${proto}:${host_port}"
        if age=$(container_age_seconds "$container") && (( age < GRACE_SECONDS )); then
            SKIPPED+="⏳ $name in grace period (age=${age}s)\n"
            continue
        fi
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

AGENT_SECRET="${AGENT_SECRET:-}"
if [ -n "$AGENT_SECRET" ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^langgraph-agent$'; then
    docker exec -e AGENT_SECRET langgraph-agent sh -c '
        curl -s -o /dev/null -w "%{http_code}" --max-time 30 \
            -X POST http://localhost:8090/api/resource_alert_check \
            -H "x-agent-secret: ${AGENT_SECRET}"
    ' >/dev/null 2>&1 || true
fi

PREV_STATE=""
[[ -f "$STATE_FILE" ]] && PREV_STATE=$(cat "$STATE_FILE" 2>/dev/null || true)

if [ -n "$ALERT" ]; then
    echo -e "HEALTH CHECK FAILED ($FAILED/$CHECKED):\n$ALERT"
    [[ -n "$SKIPPED" ]] && echo -e "skipped:\n$SKIPPED"

    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
            -d text="⚠️ HEALTH ALERT ($(date '+%H:%M')):
${ALERT}" > /dev/null 2>&1
    fi

    echo "FAILED" > "$STATE_FILE"
    exit 1
else
    echo "OK: $CHECKED/$CHECKED checks passed ($(date '+%Y-%m-%d %H:%M:%S'))"
    [[ -n "$SKIPPED" ]] && echo -e "skipped:\n$SKIPPED"

    if [[ "$PREV_STATE" == "FAILED" ]] && [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_ALLOWED_USERS" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_ALLOWED_USERS}" \
            -d text="✅ RECOVERED ($(date '+%H:%M')) — $CHECKED/$CHECKED checks pass" > /dev/null 2>&1
    fi

    echo "OK" > "$STATE_FILE"
    exit 0
fi
