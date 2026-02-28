#!/bin/bash
set -e

chown -R appuser:appgroup /app/sessions 2>/dev/null || true

graceful_shutdown() {
  echo "Shutting down telegram bot..."
  exit 0
}
trap graceful_shutdown SIGTERM SIGINT

echo "Starting telegram bot..."
exec python main.py "$@"
