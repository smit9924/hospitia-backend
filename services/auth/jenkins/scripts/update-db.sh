#!/usr/bin/env bash

set -Eeuo pipefail

echo "Running database migrations..."

cd /app/auth/database

uv run alembic upgrade head

echo "Starting application..."

exec "$@"