# 8x8 Voice API (CPaaS) - Appointment Confirmation System

This project implements an automated appointment confirmation system using the 8x8 Voice API. It makes outbound calls to customers to confirm their appointments using an Interactive Voice Response (IVR) system.

## Common Use Cases

This system can be adapted for various scenarios, including:

- Medical appointments and healthcare consultations
- Restaurant reservations and dining bookings
- Salon and spa services
- Vehicle service appointments and maintenance
- Professional consultations (legal, financial, real estate)

Each use case can be implemented by customizing the voice prompts and workflow in the application configuration.

## Features

- Outbound calls to confirm appointments or reservations
- Interactive voice menu for customers to confirm or cancel
- Real-time webhook handling for call events
- Session tracking for call state management
- Detailed logging for debugging and monitoring

## Prerequisites

- Docker and Docker Compose
- 8x8 Connect Account with:
  - API Key
  - Subaccount ID
  - Virtual Number (for outbound calls)
- Ngrok account with authtoken and a static domain for local testing

## Setting Up Ngrok

This project requires ngrok with a static domain for webhook handling:

- **Ngrok account**: Sign up at [ngrok.com](https://ngrok.com/signup)
- **Static domain**: Head over to https://dashboard.ngrok.com/domains to create a static domain (Limited to 1 static url for free ngrok accounts)
- **Authtoken**: Go to https://dashboard.ngrok.com/authtokens to create an authtoken

While there are alternatives to ngrok, such as:
- Deploying to a cloud provider (AWS, GCP, Azure)
- Using other tunneling services like [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/)
- Setting up your own reverse proxy with a static IP

Please note that this project's Docker configuration, scripts, and overall implementation are specifically designed for ngrok. Using any alternative would require significant changes to the Docker setup, configuration files, and possibly the application code.

## Quick Start with Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/harrism04/voice_restaurant_ivr.git
   cd voice_restaurant_ivr
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your credentials:
   ```
   EIGHT_X_EIGHT_API_KEY=your_api_key_from_connect_portal
   EIGHT_X_EIGHT_SUBACCOUNT_ID=your_subaccount_id
   OUTBOUND_PHONE_NUMBER=your_virtual_number  # Must be in international format e.g for SG +6591234567
   WEBHOOK_AUTH_TOKEN=your_randomly_generated_webhook_auth_token
   WEBHOOK_BASE_URL=your_static_ngrok_domain  # e.g., https://your-domain.ngrok-free.app
   NGROK_AUTHTOKEN=your_ngrok_authtoken
   ```
   Note: The `OUTBOUND_PHONE_NUMBER` is used as the source number for all outbound calls. It must be a valid 8x8 virtual number configured in your account. Reach out to cpaas-support@8x8.com or your account manager if unsure.

3. Configure your static ngrok domain:
   - Go to https://dashboard.ngrok.com/domains to find your static ngrok domain or create one if you haven't already.
   - Update `WEBHOOK_BASE_URL` in your `.env` file with your static ngrok domain.
   - Edit the `docker-compose.yml` file and update the `--domain` parameter in the `NGROK_OPTS` environment variable with your static domain:
     ```yaml
     - 'NGROK_OPTS=--log=stdout --domain=your-domain.ngrok-free.app'
     ```
   
   Note: The ngrok configuration is automatically generated inside the container, so you don't need to manually create or edit an ngrok.yml file.

4. Configure webhooks in 8x8 Connect console or [via API](https://developer.8x8.com/connect/reference/create-a-new-webhook):
   - VCA Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vca`
   - VSS Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vss` 

5. Start the application:
   ```bash
   # For first time setup, use --build flag
   docker-compose up -d --build
   
   # For subsequent starts
   docker-compose up -d
   ```
   
   To check the status of your services:
   ```bash
   docker ps
   ```
   
   To view the ngrok tunnel URL:
   ```bash
   curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*'
   ```
   
   To stop the services:
   ```bash
   docker-compose down
   ```

The application is now ready to handle calls!

## Manual Installation (Alternative)

If you prefer not to use Docker, you can install the application manually:

1. Clone the repository:
   ```bash
   git clone https://github.com/harrism04/voice_restaurant_ivr.git
   cd voice_restaurant_ivr
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your credentials:
   ```
   EIGHT_X_EIGHT_API_KEY=your_api_key_from_connect_portal
   EIGHT_X_EIGHT_SUBACCOUNT_ID=your_subaccount_id
   OUTBOUND_PHONE_NUMBER=your_virtual_number  # Must be in international format e.g for SG +6591234567
   WEBHOOK_AUTH_TOKEN=your_randomly_generated_webhook_auth_token
   WEBHOOK_BASE_URL=your_static_ngrok_domain  # e.g., https://your-domain.ngrok-free.app
   NGROK_AUTHTOKEN=your_ngrok_authtoken
   ```
   Note: The `OUTBOUND_PHONE_NUMBER` is used as the source number for all outbound calls. It must be a valid 8x8 virtual number configured in your account. Reach out to cpaas-support@8x8.com or your account manager if unsure.

5. Configure your static ngrok domain:
   - Go to https://dashboard.ngrok.com/domains to find your static ngrok domain or create one if you haven't already.
   - Update `WEBHOOK_BASE_URL` in your `.env` file with your static ngrok domain.

6. Configure webhooks in 8x8 Connect console:
   - VCA Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vca`
   - VSS Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vss`
   
   Configure authentication as described in the Docker setup section (step 4).

7. Set up ngrok configuration:
   Create a file named `ngrok.yml` with the following content:
   ```yaml
   version: 2
   authtoken: your_ngrok_authtoken
   web_addr: 0.0.0.0:4040
   tunnels:
     http:
       addr: 5678
       proto: http
       domain: your-static-domain.ngrok-free.app  # Use your static domain here
       basic_auth:
         - "admin:your_webhook_auth_token"  # Same as WEBHOOK_AUTH_TOKEN in .env
   ```

8. Start ngrok to create a tunnel for webhooks:
   ```bash
   # Start ngrok with the configuration file
   ngrok start --config ngrok.yml http
   ```
   This command starts the tunnel named "http" defined in your configuration file.
   
   Verify that ngrok is using your static domain by checking the output. You should see a line like:
   ```
   started tunnel http -> http://localhost:5678
   url: https://your-static-domain.ngrok-free.app
   ```

9. Start the FastAPI server:
   ```bash
   python -m uvicorn main:app --reload --port 5678
   ```

## Making a Test Call

Use curl or any API client to make a test call. First, create a Base64 encoded string of `admin:your_webhook_auth_token`:

```bash
# On Mac/Linux
echo -n "admin:your_webhook_auth_token" | base64

# On Windows PowerShell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("admin:your_webhook_auth_token"))
```

Then use the encoded string in your API call:

```bash
curl --location 'http://localhost:5678/api/make-call' \
--header 'Authorization: Basic YOUR_BASE64_ENCODED_STRING' \
--header 'Content-Type: application/json' \
--data '{
    "orderId": "APT123",
    "customerPhone": "+6591234567",
    "businessName": "Business Name",
    "appointmentTime": "2025-04-20T19:30:00Z"
}'
```

Example:
- If your `WEBHOOK_AUTH_TOKEN` is `secret123`
- Base64 encode `admin:secret123` → `YWRtaW46c2VjcmV0MTIz`
- Use `Authorization: Basic YWRtaW46c2VjcmV0MTIz` in the header

Note: 
- The call will be made from the OUTBOUND_PHONE_NUMBER specified in your .env file

## API Documentation

### Endpoints

1. `POST /api/make-call`
   - Makes an outbound call to confirm an appointment
   - Uses OUTBOUND_PHONE_NUMBER from .env as the source number
   - Requires Basic Auth (admin:WEBHOOK_AUTH_TOKEN encoded in Base64)
   - Request body example:
     ```json
     {
         "orderId": "APT123",
         "customerPhone": "+6591234567",
         "businessName": "Business Name",
         "appointmentTime": "2025-04-20T19:30:00Z"
     }
     ```

2. `POST /api/webhooks/vca`
   - Handles Voice Call Action webhooks from 8x8

3. `POST /api/webhooks/vss`
   - Handles Voice Session Summary webhooks from 8x8

### Call Flow

1. System makes an outbound call to the customer
2. Plays a message with appointment details
3. Customer inputs DTMF:
   - Press 1 to confirm
   - Press 0 to cancel
4. System responds with confirmation/cancellation message
5. Call ends with appropriate status

## Project Structure

```
voice_restaurant_ivr/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container configuration for main app
├── Dockerfile.ngrok     # Docker container configuration for ngrok
├── docker-compose.yml   # Docker services orchestration
├── generate_ngrok_config.sh # Script to generate ngrok config
├── start_ngrok.sh       # Script to start ngrok in container
├── .env                 # Environment variables (not in repo)
├── .env.example         # Environment variables template
├── README.md            # This file
├── api_reference.md     # Detailed API documentation
├── flow_diagram_simple.md # Simple flow diagram
├── flow_diagram_detailed.md # Detailed flow diagram
├── plan.md              # Project plan
├── .dockerignore        # Files to exclude from Docker build
├── .gitignore           # Files to exclude from git
├── images/              # Screenshots and images for documentation
└── voice_requirements.md # Project requirements
```

Note: The ngrok.yml file is not included in the repository as it's generated dynamically by the generate_ngrok_config.sh script when using Docker. For manual installation, you'll need to create this file by copying and modifying the ngrok.yml.example file as described in the manual installation section.

## Logging

The application includes detailed console logging for:
- Incoming requests (method, URL, headers)
- Phone number formatting and validation
- API calls to 8x8 (requests and responses)
- Call state changes
- Webhook events
- Error conditions

Logs are written to stdout and can be monitored in real-time through the console.

## Error Handling

The application includes robust error handling for:
- Missing or invalid credentials
- Failed API calls
- Invalid webhook data
- Missing session data
- Authentication failures

## Security

- Basic Authentication for API endpoints
- Token-based authentication for webhooks
- Environment variables for sensitive data
