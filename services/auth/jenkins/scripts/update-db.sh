#!/usr/bin/env bash

set -Eeuo pipefail

echo "Running database migrations..."

cd /app/auth/database

alembic -c ./alembic.ini upgrade head

echo "Starting application..."

exec "$@"