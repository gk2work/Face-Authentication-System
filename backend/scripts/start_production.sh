#!/bin/bash

# Production startup script for Face Authentication System
# Supports multiple worker processes for horizontal scaling

set -e

# Default configuration
WORKERS=${WORKERS:-4}
HOST=${API_HOST:-0.0.0.0}
PORT=${API_PORT:-8000}
TIMEOUT=${TIMEOUT:-120}
LOG_LEVEL=${LOG_LEVEL:-info}

echo "========================================="
echo "Face Authentication System - Production"
echo "========================================="
echo "Workers: $WORKERS"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Timeout: ${TIMEOUT}s"
echo "Log Level: $LOG_LEVEL"
echo "========================================="

# Check if gunicorn is available
if command -v gunicorn &> /dev/null; then
    echo "Starting with Gunicorn + Uvicorn workers..."
    exec gunicorn app.main:app \
        --workers $WORKERS \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind $HOST:$PORT \
        --timeout $TIMEOUT \
        --log-level $LOG_LEVEL \
        --access-logfile - \
        --error-logfile - \
        --graceful-timeout 30 \
        --keep-alive 5
else
    echo "Gunicorn not found, starting with Uvicorn..."
    exec uvicorn app.main:app \
        --host $HOST \
        --port $PORT \
        --workers $WORKERS \
        --log-level $LOG_LEVEL \
        --timeout-keep-alive 5
fi
