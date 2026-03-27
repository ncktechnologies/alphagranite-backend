#!/bin/bash

set -euo pipefail

STACK="${1:-}"
if [[ -z "$STACK" ]]; then
  echo "Usage: $0 <dev|staging>"
  exit 1
fi

if [[ "$STACK" != "dev" && "$STACK" != "staging" ]]; then
  echo "Invalid stack: $STACK"
  echo "Usage: $0 <dev|staging>"
  exit 1
fi

ENV_FILE=".env.${STACK}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE"
  echo "Create it from compose.${STACK}.env.example"
  exit 1
fi

PROJECT_NAME="$(grep -E '^COMPOSE_PROJECT_NAME=' "$ENV_FILE" | head -n1 | cut -d '=' -f2-)"
if [[ -z "$PROJECT_NAME" ]]; then
  echo "COMPOSE_PROJECT_NAME is required in $ENV_FILE"
  exit 1
fi

echo "Deploying stack: $STACK"
echo "Project name: $PROJECT_NAME"
echo "Env file: $ENV_FILE"

mkdir -p static/uploads static/defaults logs

# Use project + env file so stacks stay isolated and can run together.
docker compose --env-file "$ENV_FILE" -p "$PROJECT_NAME" up -d --build

echo "Deployment complete for $STACK"
docker compose --env-file "$ENV_FILE" -p "$PROJECT_NAME" ps
