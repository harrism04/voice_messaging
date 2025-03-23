#!/bin/bash
set -e

# Check if NGROK_AUTHTOKEN is set
if [ -z "$NGROK_AUTHTOKEN" ]; then
  echo "Error: NGROK_AUTHTOKEN is not set. Please set this environment variable."
  exit 1
fi

# Set default values if not provided
TARGET_HOST=${TARGET_HOST:-"localhost"}
TARGET_PORT=${TARGET_PORT:-"80"}
NGROK_PORT="${TARGET_HOST}:${TARGET_PORT}"

# Extract domain name from WEBHOOK_BASE_URL if it exists
DOMAIN_FLAG=""
if [ ! -z "$WEBHOOK_BASE_URL" ]; then
  # Extract domain from URL, removing https:// prefix
  DOMAIN_NAME=$(echo "$WEBHOOK_BASE_URL" | sed -e 's|^https://||' -e 's|/.*$||')
  echo "Using static domain: $DOMAIN_NAME"
  DOMAIN_FLAG="--domain=$DOMAIN_NAME"
fi

# Wait for backend to be available if we're in a Docker Compose setup
if [[ "$NGROK_PORT" == *":"* ]]; then
  # Extract hostname and port
  IFS=':' read -r HOST PORT <<< "$NGROK_PORT"
  
  echo "Waiting for $HOST:$PORT to be available..."
  until nc -z -w 2 "$HOST" "$PORT" 2>/dev/null; do
    echo "Waiting for $HOST:$PORT..."
    sleep 2
  done
  echo "$HOST:$PORT is available. Starting ngrok."
fi

# Generate ngrok config with actual values
/app/generate_ngrok_config.sh

# Start ngrok with explicit config file and domain flag
echo "Starting ngrok with target $NGROK_PORT using config file /etc/ngrok.yml and domain: $DOMAIN_NAME"
if [ ! -z "$DOMAIN_FLAG" ]; then
  exec ngrok http --config=/etc/ngrok.yml $DOMAIN_FLAG "$NGROK_PORT"
else
  exec ngrok http --config=/etc/ngrok.yml "$NGROK_PORT"
fi