#!/bin/sh
set -e

CONFIG_TEMPLATE="/etc/alertmanager/alertmanager.yml.tmpl"
CONFIG_OUT="/etc/alertmanager/alertmanager.yml"

sed \
  -e "s|PLACEHOLDER_BOT_TOKEN|${TELEGRAM_BOT_TOKEN}|g" \
  -e "s|PLACEHOLDER_CHAT_ID|${TELEGRAM_CHAT_ID}|g" \
  "$CONFIG_TEMPLATE" > "$CONFIG_OUT"

exec /bin/alertmanager "$@"
