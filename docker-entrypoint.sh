#!/bin/sh
set -eu

if [ "${1:-}" = "serve" ]; then
    alembic upgrade head
    exec uvicorn infra.api.app:create_app --factory \
        --host 0.0.0.0 \
        --port "${PORT:-8000}"
fi

exec "$@"
