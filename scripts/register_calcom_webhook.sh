#!/usr/bin/env bash
set -euo pipefail

# Registers the n8n Cal.com webhook by inserting a row into Cal.com's
# Webhook table. Used when API key is not available (Cal.com self-host
# API keys require a commercial license).

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "DATABASE_URL not set (source /opt/ai-secretary/.env first)" >&2
    exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
    echo "installing postgresql-client..."
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -yq postgresql-client
fi

SUBSCRIBER_URL="${SUBSCRIBER_URL:-https://${N8N_HOST}/webhook/calcom-booking}"
USER_ID="${CALCOM_USER_ID:-1}"
WEBHOOK_ID="wh_n8n_agent_$(date +%s)"

psql "$DATABASE_URL" <<SQL
DELETE FROM "Webhook" WHERE "subscriberUrl" = '$SUBSCRIBER_URL';

INSERT INTO "Webhook" (id, "userId", "subscriberUrl", active, "eventTriggers", version)
VALUES (
  '$WEBHOOK_ID',
  $USER_ID,
  '$SUBSCRIBER_URL',
  true,
  ARRAY['BOOKING_CREATED', 'BOOKING_RESCHEDULED', 'BOOKING_CANCELLED', 'MEETING_ENDED']::"WebhookTriggerEvents"[],
  '2021-10-20'
);
SQL

echo "registered:"
psql "$DATABASE_URL" -c 'SELECT id, "subscriberUrl", "eventTriggers", active FROM "Webhook";'
