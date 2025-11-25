#!/bin/sh
set -e

# Replace localhost with host.docker.internal for Docker on macOS/Windows
# This allows the container to connect to services running on the host
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's/@localhost:/@host.docker.internal:/g')
    echo "Modified DATABASE_URL for Docker networking"
fi

# Run migration script
python scripts/auto_migrate.py

# Start the application
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --workers 4
