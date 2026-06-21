#!/usr/bin/env bashio
# shellcheck shell=bash
set -e

bashio::log.info "Starting ha-todo-manager..."

DB_PATH=/data/todo.db
LOG_LEVEL=$(bashio::config 'log_level' 'info')

# ha_webhook_secret / person_sync_interval_hours / materialise_interval_minutes
# are declared in config.yaml but not wired into the CLI yet — see
# spec/roadmap.md (Phase 2/3).
exec python -m ha_todo_manager \
    --host 0.0.0.0 \
    --port 8100 \
    --db-path "${DB_PATH}" \
    --log-level "${LOG_LEVEL}"
