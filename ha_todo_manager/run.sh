#!/usr/bin/env bashio
# shellcheck shell=bash
set -e

bashio::log.info "Starting ha-todo-manager..."

DB_PATH=/data/todo.db
LOG_LEVEL=$(bashio::config 'log_level' 'info')
WEBHOOK_SECRET=$(bashio::config 'ha_webhook_secret' '')
PERSON_SYNC_INTERVAL_HOURS=$(bashio::config 'person_sync_interval_hours' '6')
MATERIALISE_INTERVAL_MINUTES=$(bashio::config 'materialise_interval_minutes' '60')

exec python -m ha_todo_manager \
    --host 0.0.0.0 \
    --port 8100 \
    --db-path "${DB_PATH}" \
    --log-level "${LOG_LEVEL}" \
    --webhook-secret "${WEBHOOK_SECRET}" \
    --person-sync-interval-hours "${PERSON_SYNC_INTERVAL_HOURS}" \
    --materialise-interval-minutes "${MATERIALISE_INTERVAL_MINUTES}"
