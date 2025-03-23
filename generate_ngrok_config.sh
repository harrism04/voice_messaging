#!/bin/bash
set -e

# Check if NGROK_AUTHTOKEN is set
if [ -z "$NGROK_AUTHTOKEN" ]; then
  echo "Error: NGROK_AUTHTOKEN is not set. Please set this environment variable."
  exit 1
fi

# Extract domain name from WEBHOOK_BASE_URL if it exists
DOMAIN_NAME=""
if [ ! -z "$WEBHOOK_BASE_URL" ]; then
  # Extract domain from URL, removing https:// prefix
  DOMAIN_NAME=$(echo "$WEBHOOK_BASE_URL" | sed -e 's|^https://||' -e 's|/.*$||')
  echo "Using static domain: $DOMAIN_NAME"
fi

# Create ngrok.yml with actual values
cat > /etc/ngrok.yml << EOF
version: 2
authtoken: $NGROK_AUTHTOKEN
web_addr: 0.0.0.0:4040
tunnels:
  http:
    addr: backend:5678
    proto: http
    basic_auth:
      - "admin:0f5332e8ace371bc0aa5fa4ec058050fa048c03ec5f95ffdfbbf2fd95046720"
EOF

echo "Generated ngrok.yml with actual values"
cat /etc/ngrok.yml 