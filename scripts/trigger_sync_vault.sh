#!/usr/bin/env bash
set -euo pipefail

AGENT_URL="${AGENT_URL:-http://127.0.0.1:8090}"
AGENT_SECRET="${AGENT_SECRET:-}"

if [[ -z "${AGENT_SECRET}" ]]; then
  echo "AGENT_SECRET not set" >&2
  exit 1
fi

# Sentinel "container" skips host-level curl and exec inside the agent
# container, which is how we reach it from a VPS cron without exposing
# the port on the host.
if [[ "${AGENT_URL}" == "container" ]]; then
  docker exec langgraph-agent sh -c "
    curl -sS --max-time 300 -w '\nHTTP %{http_code}\n' \
      -H 'X-Agent-Secret: ${AGENT_SECRET}' \
      -H 'Content-Type: application/json' \
      -d '{}' \
      http://localhost:8090/api/sync_vault
  "
else
  curl -sS --max-time 300 -w '\nHTTP %{http_code}\n' \
    -H "X-Agent-Secret: ${AGENT_SECRET}" \
    -H 'Content-Type: application/json' \
    -d '{}' \
    "${AGENT_URL}/api/sync_vault"
fi
