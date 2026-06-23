#!/usr/bin/env bashio
# shellcheck shell=bash
set -e

bashio::log.info "Starting ha-shopping-list..."

DB_PATH=/data/shoppinglist.db
LOG_LEVEL=$(bashio::config 'log_level' 'info')
API_KEY=$(bashio::config 'api_key' '')
exec python -m ha_shopping_list \
    --host 0.0.0.0 \
    --port 8099 \
    --db-path "${DB_PATH}" \
    --log-level "${LOG_LEVEL}" \
    --api-key "${API_KEY}"
