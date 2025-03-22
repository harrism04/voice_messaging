from fastapi import FastAPI, HTTPException, Header, Request
from typing import Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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

# Constants
VOICE_API_BASE_URL = "https://voice.wavecell.com/api/v1"

# Models
class Appointment(BaseModel):
    orderId: str
    customerPhone: str
    businessName: str
    appointmentTime: datetime

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
async def make_call(appointment: Appointment, authorization: str = Header(None)):
    logger.info(f"Request body: {appointment.dict()}")
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
        # Format time for voice message
        formatted_time = appointment.appointmentTime.strftime("%I:%M %p")
        
        # Generate client action ID with readable datetime
        formatted_datetime = appointment.appointmentTime.strftime("%Y%m%d_%H%M")
        sanitized_business_name = appointment.businessName.replace(' ', '_')
        client_action_id = f"{appointment.orderId}_{formatted_datetime}_{sanitized_business_name}"
        
        # Set validUntil to 1 hour from now
        valid_until = (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Format phone numbers for API
        source_number = outbound_phone.lstrip('+')
        destination_number = appointment.customerPhone.lstrip('+')
        
        # Log phone number details for debugging
        logger.info(f"Phone number details:")
        logger.info(f"Original source (from .env): {outbound_phone}")
        logger.info(f"Formatted source: {source_number}")
        logger.info(f"Original destination: {appointment.customerPhone}")
        logger.info(f"Formatted destination: {destination_number}")
        
        # Validate Singapore phone numbers (must be 65 + 8 digits)
        def validate_sg_number(number: str, number_type: str) -> str:
            if not number.isdigit():
                raise ValueError(f"{number_type} contains non-digit characters: {number}")
            if not number.startswith('65'):
                number = '65' + number.lstrip('0')
            if len(number) != 10:  # 65 + 8 digits
                raise ValueError(f"{number_type} must be 10 digits (65 + 8 digits), got {len(number)} digits: {number}")
            return number
        
        # Format and validate numbers
        source_number = validate_sg_number(source_number, "Source number")
        destination_number = validate_sg_number(destination_number, "Destination number")
        
        logger.info(f"Final formatted numbers:")
        logger.info(f"Source: {source_number}")
        logger.info(f"Destination: {destination_number}")
        
        # Prepare the initial call request
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
                    "action": "sayAndCapture",
                    "params": {
                        "promptMessage": f"Hello, you have an appointment at {appointment.businessName} at {formatted_time} made through our platform. Will you be arriving on time? If yes, press one. If you wish to cancel, press zero.",
                        "voiceProfile": "en-US-BenjaminRUS",
                        "repetition": 2,
                        "speed": 1,
                        "minDigits": 1,
                        "maxDigits": 1,
                        "digitTimeout": 10000,
                        "overallTimeout": 10000,
                        "completeOnHash": False,
                        "noOfTries": 2,
                        "successMessage": None,
                        "failureMessage": "Invalid input, please try again"
                    }
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
                "state": "initial",
                "appointment": appointment.dict(),
                "formatted_time": formatted_time,
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
    dtmf_input = None
    event_data = payload.get("eventData", {})
    
    if isinstance(event_data, dict):
        dtmf_input = event_data.get("dtmf")
    elif isinstance(event_data, str):
        dtmf_input = event_data
    
    logger.info(f"Extracted DTMF input: {dtmf_input}")
    
    client_action_id = payload.get("clientActionId")
    call_data = call_store.get_call(session_id)
    
    if not call_data:
        client_action_id = client_action_id or f"recovered_{session_id}"
        call_data = {
            "state": "initial",
            "client_action_id": client_action_id,
            "session_id": session_id
        }
        call_store.add_call(session_id, call_data)
    
    # Process the IVR response based on the current state and input
    response = None
    if dtmf_input:
        if dtmf_input == "1":
            response = {
                "clientActionId": call_data["client_action_id"],
                "callflow": [
                    {
                        "action": "say",
                        "params": {
                            "text": "Thank you for confirming. We look forward to seeing you at your appointment time.",
                            "voiceProfile": "en-US-BenjaminRUS",
                            "repetition": 1,
                            "speed": 1
                        }
                    },
                    {
                        "action": "hangup",
                        "params": {}
                    }
                ]
            }
            call_data["state"] = "confirmed"
        elif dtmf_input == "0":
            response = {
                "clientActionId": call_data["client_action_id"],
                "callflow": [
                    {
                        "action": "say",
                        "params": {
                            "text": "Your appointment has been cancelled. Thank you for letting us know.",
                            "voiceProfile": "en-US-BenjaminRUS",
                            "repetition": 1,
                            "speed": 1
                        }
                    },
                    {
                        "action": "hangup",
                        "params": {}
                    }
                ]
            }
            call_data["state"] = "cancelled"
    
    if not response:
        if call_data["state"] == "initial":
            response = {
                "clientActionId": call_data["client_action_id"],
                "callflow": []
            }
        else:
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
