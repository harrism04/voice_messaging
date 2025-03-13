#!/bin/bash
set -e

# Check if NGROK_AUTHTOKEN is set
if [ -z "$NGROK_AUTHTOKEN" ]; then
  echo "Error: NGROK_AUTHTOKEN is not set. Please set this environment variable."
  exit 1
fi

# Set default values if not provided
NGROK_PORT=${NGROK_PORT:-"80"}
NGROK_OPTS=${NGROK_OPTS:-""}

# Wait for reservation-system to be available if we're in a Docker Compose setup
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

# Start ngrok with explicit config file
echo "Starting ngrok with port $NGROK_PORT and options: $NGROK_OPTS using config file /etc/ngrok.yml"
exec ngrok http --config=/etc/ngrok.yml $NGROK_OPTS $NGROK_PORT