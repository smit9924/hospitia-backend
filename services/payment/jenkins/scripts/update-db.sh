#!/usr/bin/env bash

set -Eeuo pipefail

echo "Running database migrations..."

# Run migration from /app directory instead of getting inside auth/database directory
# to avoid module auth not found error when running alembic command
alembic -c ./payment/database/alembic.ini upgrade head

echo "Starting application..."

exec "$@"