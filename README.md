# 8x8 Voice API - Restaurant Reservation Confirmation System

This project implements an automated restaurant reservation confirmation system using the 8x8 Voice API. It makes outbound calls to customers to confirm their restaurant reservations using an Interactive Voice Response (IVR) system.

## Features

- Outbound calls to confirm restaurant reservations
- Interactive voice menu for customers to confirm or cancel reservations
- Real-time webhook handling for call events
- Session tracking for call state management
- Detailed logging for debugging and monitoring

## Prerequisites

- Docker and Docker Compose
- 8x8 Account with:
  - API Key
  - Subaccount ID
  - Virtual Number (for outbound calls)
- Ngrok account with authtoken

## Quick Start with Docker

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
   OUTBOUND_PHONE_NUMBER=your_virtual_number  # Must be in Singapore format: +6568332042
   WEBHOOK_AUTH_TOKEN=your_randomly_generated_webhook_auth_token
   WEBHOOK_BASE_URL=your_ngrok_url
   NGROK_AUTHTOKEN=your_ngrok_authtoken
   ```
   Note: The `OUTBOUND_PHONE_NUMBER` is used as the source number for all outbound calls. It must be a valid 8x8 virtual number in Singapore format.

3. Start the application:
   ```bash
   docker-compose up --build
   ```

4. Get your public URL:
   - Open http://localhost:4040 in your browser
   - Copy the HTTPS URL (e.g., `https://xxxx-xx-xx-xxx-xx.ngrok-free.app`)
   - Update `WEBHOOK_BASE_URL` in your `.env` file with this URL

5. Configure webhooks in 8x8 Connect console:
   - VCA Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vca`
   - VSS Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vss`

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
   OUTBOUND_PHONE_NUMBER=your_virtual_number
   WEBHOOK_AUTH_TOKEN=your_randomly_generated_webhook_auth_token
   WEBHOOK_BASE_URL=your_ngrok_url
   ```
   Note: The `OUTBOUND_PHONE_NUMBER` is used as the source number for all outbound calls. It must be a valid 8x8 virtual number and configured in your subAccount. Confirm with cpaas-support@8x8.com if unsure.

## Running the Application

1. Set up ngrok configuration:
   ```bash
   cp ngrok.yml.example ngrok.yml
   ```
   Edit `ngrok.yml` and fill in your credentials:
   - `authtoken`: Your ngrok authentication token
   - `basic_auth`: Use the same webhook auth token as in `.env`
   - `oauth`: (Optional) Your Google OAuth credentials if using OAuth authentication

2. Start ngrok to create a tunnel for webhooks:
   ```bash
   ngrok start --config ngrok.yml 8x8_voice
   ```
   Copy the HTTPS URL (e.g., `https://xxxx-xx-xx-xxx-xx.ngrok-free.app`) and update `WEBHOOK_BASE_URL` in your `.env` file.

3. Start the FastAPI server:
   ```bash
   python -m uvicorn main:app --reload --port 5678
   ```

4. Configure webhooks in 8x8 Connect console:
   - VCA Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vca`
   - VSS Webhook URL: `{WEBHOOK_BASE_URL}/api/webhooks/vss`

## Making a Test Call

Use curl or any API client to make a test call:

```bash
curl --location 'http://localhost:5678/api/make-call' \
--header 'Authorization: Basic EIGHT_X_EIGHT_API_KEY' \
--header 'Content-Type: application/json' \
--data '{
    "orderId": "RES123",
    "customerPhone": "+6591234567",
    "restaurantName": "Test Restaurant",
    "reservationTime": "2025-04-20T19:30:00Z"
}'
```

Note: Replace the Authorization header with your Base64 encoded `admin:WEBHOOK_AUTH_TOKEN`.

## API Documentation

### Endpoints

1. `POST /api/make-call`
   - Makes an outbound call to confirm a reservation
   - Uses OUTBOUND_PHONE_NUMBER from .env as the source number
   - Requires Basic Auth
   - Request body example:
     ```json
     {
         "orderId": "RES123",
         "customerPhone": "+6591234567",
         "restaurantName": "Test Restaurant",
         "reservationTime": "2025-04-20T19:30:00Z"
     }
     ```


2. `POST /api/webhooks/vca`
   - Handles Voice Call Action webhooks
   - Requires webhook authentication token

3. `POST /api/webhooks/vss`
   - Handles Voice Session Summary webhooks
   - Requires webhook authentication token

### Call Flow

1. System makes an outbound call to the customer
2. Plays a message with reservation details
3. Customer inputs DTMF:
   - Press 1 to confirm
   - Press 0 to cancel
4. System responds with confirmation/cancellation message
5. Call ends with appropriate status

## Project Structure

```
8x8_voice/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker container configuration
├── docker-compose.yml  # Docker services orchestration
├── .env                # Environment variables (not in repo)
├── .env.example        # Environment variables template
├── README.md           # This file
├── api_reference.md    # Detailed API documentation
├── examplerequests.md  # Example API requests
├── .dockerignore       # Files to exclude from Docker build
├── ngrok.yml          # Ngrok configuration (not in repo)
├── ngrok.yml.example   # Ngrok configuration template
└── voice_requirements.md # Project requirements
```

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
- No hardcoded credentials


