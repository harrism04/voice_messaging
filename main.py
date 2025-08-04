from fastapi import FastAPI, HTTPException, Header, Request
from typing import Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import httpx
import os
import json
import requests
import docker
import time
import logging
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Add health endpoint for Docker health checks
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Constants
VOICE_API_BASE_URL = "https://voice.wavecell.com/api/v1"

# Models
class MessageCall(BaseModel):
    messageId: str
    customerPhone: str
    message: str
    repetition: int = 2  # How many times to repeat the message

# In-memory store for active calls
class CallStore:
    def __init__(self):
        self.calls = {}
        
    def add_call(self, session_id: str, data: dict):
        logger.info(f"Adding call data for session {session_id}")
        logger.info(f"Current store before adding: {self.calls}")
        self.calls[session_id] = data
        logger.info(f"Current store after adding: {self.calls}")
        
    def get_call(self, session_id: str) -> Optional[dict]:
        logger.info(f"Retrieving call data for session {session_id}")
        logger.info(f"Current store: {self.calls}")
        return self.calls.get(session_id)

# Initialize call store
call_store = CallStore()

# Authentication middleware
async def verify_auth(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # For webhook endpoints
    if authorization == os.getenv("WEBHOOK_AUTH_TOKEN"):
        return True
        
    # For other endpoints (Basic auth)
    if not authorization.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    try:
        import base64
        credentials = base64.b64decode(authorization[6:]).decode('utf-8')
        username, password = credentials.split(':')
        if username == "admin" and password == os.getenv("WEBHOOK_AUTH_TOKEN"):
            return True
    except Exception:
        pass
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"\n🔔 Incoming Request 🔔")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Headers: {request.headers}")
    
    response = await call_next(request)
    return response

# Make call endpoint
@app.post("/api/make-call")
async def make_call(message_call: MessageCall, authorization: str = Header(None)):
    logger.info(f"Request body: {message_call.dict()}")
    logger.info(f"Authorization header: {authorization}")
    # Get environment variables
    api_key = os.getenv("EIGHT_X_EIGHT_API_KEY")
    subaccount_id = os.getenv("EIGHT_X_EIGHT_SUBACCOUNT_ID")
    outbound_phone = os.getenv("OUTBOUND_PHONE_NUMBER")
    
    # Validate all required credentials
    missing_vars = []
    if not api_key:
        missing_vars.append("EIGHT_X_EIGHT_API_KEY")
    if not subaccount_id:
        missing_vars.append("EIGHT_X_EIGHT_SUBACCOUNT_ID")
    if not outbound_phone:
        missing_vars.append("OUTBOUND_PHONE_NUMBER")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Configuration error",
                "details": error_msg
            }
        )
    
    try:
        # Generate client action ID with timestamp
        formatted_datetime = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        client_action_id = f"{message_call.messageId}_{formatted_datetime}"
        
        # Set validUntil to 1 hour from now
        valid_until = (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Format phone numbers for API
        source_number = outbound_phone.lstrip('+')
        destination_number = message_call.customerPhone.lstrip('+')
        
        # Log phone number details for debugging
        logger.info(f"Phone number details:")
        logger.info(f"Original source (from .env): {outbound_phone}")
        logger.info(f"Formatted source: {source_number}")
        logger.info(f"Original destination: {appointment.customerPhone}")
        logger.info(f"Formatted destination: {destination_number}")

        # Validate international phone numbers
        def validate_number(number: str, number_type: str) -> str:
            # Strip all non-digits
            number = ''.join(c for c in number if c.isdigit())
        
            # Basic validation
            if len(number) < 7 or len(number) > 15:
                raise ValueError(f"Invalid {number_type} length: {number}")
            return number

        # Format and validate numbers
        source_number = validate_number(source_number, "Source number")
        destination_number = validate_number(destination_number, "Destination number")
        
        logger.info(f"Final formatted numbers:")
        logger.info(f"Source: {source_number}")
        logger.info(f"Destination: {destination_number}")
        
        # Prepare the call request with simple message delivery
        request_body = {
            "clientActionId": client_action_id,
            "validUntil": valid_until,
            "callflow": [
                {
                    "action": "makeCall",
                    "params": {
                        "source": source_number,
                        "destination": destination_number
                    }
                },
                {
                    "action": "say",
                    "params": {
                        "text": message_call.message,
                        "voiceProfile": "en-US-BenjaminRUS",
                        "repetition": message_call.repetition,
                        "speed": 1
                    }
                },
                {
                    "action": "hangup",
                    "params": {}
                }
            ]
        }
        
        api_url = f"{VOICE_API_BASE_URL}/subaccounts/{subaccount_id}/callflows"
        
        # Make API call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            # Log response status and data
            logger.info(f"8x8 API Response Status: {response.status_code}")
            response_data = response.json()
            logger.info(f"8x8 API Response Data: {response_data}")
            
            # Check for error response
            if response.status_code >= 400:
                raise ValueError(f"8x8 API error: {response.status_code} - {response_data}")
            
            # Process response
            if "sessionId" not in response_data:
                raise ValueError(f"No sessionId in 8x8 API response: {response_data}")
                
            call_store.add_call(response_data["sessionId"], {
                "state": "message_delivered",
                "message_call": message_call.dict(),
                "client_action_id": client_action_id,
                "session_id": response_data["sessionId"]
            })
            
            return {"success": True, "data": response_data}
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error making call: {error_msg}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to make call",
                "details": error_msg
            }
        )

# VCA webhook endpoint
@app.post("/api/webhooks/vca")
async def vca_webhook(request: Request, authorization: str = Header(None)):
    
    # Get raw webhook data
    raw_body = await request.body()
    raw_json = json.loads(raw_body)
    logger.info(f"Received VCA webhook: {raw_json}")
    
    # Process webhook and prepare response
    payload = raw_json.get("payload", {})
    session_id = payload.get("sessionId")
    client_action_id = payload.get("clientActionId")
    call_data = call_store.get_call(session_id)
    
    if not call_data:
        client_action_id = client_action_id or f"recovered_{session_id}"
        call_data = {
            "state": "message_delivered",
            "client_action_id": client_action_id,
            "session_id": session_id
        }
        call_store.add_call(session_id, call_data)
    
    # For message delivery, we just acknowledge and hangup on any input
    response = {
        "clientActionId": call_data["client_action_id"],
        "callflow": [
            {
                "action": "hangup",
                "params": {}
            }
        ]
    }
    
    logger.info(f"Sending VCA webhook response: {response}")
    return JSONResponse(content=response)

# VSS webhook endpoint
@app.post("/api/webhooks/vss")
async def vss_webhook(request: Request, authorization: str = Header(None)):
    
    # Get raw webhook data
    raw_body = await request.body()
    raw_json = json.loads(raw_body)
    logger.info(f"Received VSS webhook: {raw_json}")
    
    session_id = raw_json.get("payload", {}).get("sessionId")
    if session_id:
        call_data = call_store.get_call(session_id)
        if call_data:
            call_data["state"] = "completed"
    
    response = {"status": "ok"}
    logger.info(f"Sending VSS webhook response: {response}")
    return JSONResponse(content=response)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Server starting up")
    # 8x8 API details
    api_key = os.getenv("EIGHT_X_EIGHT_API_KEY")
    subaccount_id = os.getenv("EIGHT_X_EIGHT_SUBACCOUNT_ID")
    outbound_phone = os.getenv("OUTBOUND_PHONE_NUMBER")

    # Validate all required credentials
    missing_vars = []
    if not api_key:
        missing_vars.append("EIGHT_X_EIGHT_API_KEY")
    if not subaccount_id:
        missing_vars.append("EIGHT_X_EIGHT_SUBACCOUNT_ID")
    if not outbound_phone:
        missing_vars.append("OUTBOUND_PHONE_NUMBER")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)