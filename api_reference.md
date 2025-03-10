# 8x8 Voice API Reference

## Initial Call Setup

### Make Call Request
```bash
curl -X POST "https://voice.wavecell.com/api/v1/subaccounts/${EIGHT_X_EIGHT_SUBACCOUNT_ID}/callflows" \
-H "Authorization: Bearer ${EIGHT_X_EIGHT_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
  "validUntil": "2024-01-20T20:30:00Z",
  "clientActionId": "RES123_20250520193000_TestRestaurant",
  "callflow": [
    {
      "action": "makeCall",
      "params": {
        "source": ${YOUR_VIRTUAL_NUMBER},
        "destination": ${OUTBOUND_PHONE_NUMBER}
      }
    },
    {
      "action": "sayAndCapture",
      "params": {
        "promptMessage": "Hello, you have a reservation at Test Restaurant at 7:30 PM made through our platform. Will you be arriving on time? If yes, press one. If you wish to cancel, press zero.",
        "voiceProfile": "en-US-BenjaminRUS",
        "repetition": 1,
        "speed": 1,
        "minDigits": 1,
        "maxDigits": 1,
        "digitTimeout": 10000,
        "overallTimeout": 20000,
        "completeOnHash": false,
        "noOfTries": 2,
        "successMessage": null,
        "failureMessage": "Invalid input, please try again"
      }
    }
  ]
}'
```

### Expected Response
```json
{
  "sessionId": "example-session-id-12345",
  "sessionStatus": "CREATED",
  "callFlowRequestId": "example-request-id-67890",
  "validUntil": "2024-01-20T20:30:00Z",
  "statusCode": 1,
  "statusMessage": "Created"
}
```

## VCA (Voice Call Action) Webhook

### Incoming Webhook Payload (DTMF Input)
```json
{
  "payload": {
    "eventId": "example-event-id",
    "callId": "example-call-id",
    "sessionId": "example-session-id",
    "subAccountId": "example_subaccount",
    "callStatus": "ACTION_COMPLETED",
    "callDirection": "OUTBOUND",
    "callType": "PSTN",
    "source": "+1234567890",
    "destination": "+0987654321",
    "sourceFormat": "MSISDN",
    "destinationFormat": "MSISDN",
    "sourceCountryCode": "SG",
    "destinationCountryCode": "SG",
    "sourceRefId": "example-ref",
    "callDuration": 0,
    "eventData": "1",  // The DTMF input ("1" for confirm, "0" for cancel)
    "sipCode": 200,
    "timestamp": "2025-03-10T05:31:45.971Z"
  },
  "namespace": "VOICE",
  "eventType": "CALL_ACTION",
  "description": "Action request of a call"
}
```

### Response for Confirmation (Digit 1)
```json
{
  "clientActionId": "RES123_20250520193000_TestRestaurant",
  "callflow": [
    {
      "action": "say",
      "params": {
        "text": "Thank you for confirming. We look forward to seeing you at your reservation time.",
        "voiceProfile": "en-US-BenjaminRUS",
        "speed": 1,
        "repetition": 1
      }
    },
    {
      "action": "hangup"
    }
  ]
}
```

### Response for Cancellation (Digit 0)
```json
{
  "clientActionId": "RES123_20250520193000_TestRestaurant",
  "callflow": [
    {
      "action": "say",
      "params": {
        "text": "Your reservation has been cancelled. Thank you for letting us know.",
        "voiceProfile": "en-US-BenjaminRUS",
        "speed": 1,
        "repetition": 1
      }
    },
    {
      "action": "hangup"
    }
  ]
}
```

## VSS (Voice Session Summary) Webhook

### Expected Incoming Webhook Payload
```json
{
  "payload": {
    "sessionId": "example-session-id",
    "subAccountId": "example_subaccount",
    "sessionStatus": "COMPLETED",  // or "ERROR"
    "startTime": "2025-03-10T05:31:28Z",
    "endTime": "2025-03-10T05:31:46Z",
    "lastAction": "SAY_AND_CAPTURE",
    "callCount": 1,
    "details": {
      "CallA": {
        "callId": "example-call-id",
        "callDirection": "OUTBOUND",
        "callType": "PSTN",
        "initiatedTimestamp": "2025-03-10T05:31:28Z",
        "connectedTimestamp": "2025-03-10T05:31:34Z",
        "disconnectedTimestamp": "2025-03-10T05:31:46Z",
        "source": "+1234567890",
        "destination": "+0987654321",
        "sourceFormat": "MSISDN",
        "destinationFormat": "MSISDN",
        "sourceCountryCode": "SG",
        "destinationCountryCode": "SG",
        "sourceRefId": "example-ref",
        "callStatus": "COMPLETED",
        "callDuration": 12,
        "callQuality": {
          "mos": 4.5,
          "packetLossRate": 0,
          "jitter": 20
        }
      }
    }
  },
  "namespace": "VOICE",
  "eventType": "SESSION_SUMMARY",
  "description": "Summary of a completed call session"
}
```

### Error Scenario in VSS
When there's an error in the call flow, the payload will include an `errorDetails` section:
```json
{
  "errorDetails": {
    "callFlowRequestId": "example-request-id",
    "action": "SAY_AND_CAPTURE",
    "errorMsg": "The call flow provided is invalid",
    "errorCode": -2003
  }
}
```

Common Error Codes:
- `-2003`: Invalid call flow response
- Other error codes to be documented as encountered

### Response
Simple 200 OK response is sufficient for VSS webhook.

## Notes
- All webhook endpoints require authentication token in the Authorization header
- The `clientActionId` format is: `{orderId}_{reservationTimestamp}_{sanitizedRestaurantName}`
- The `validUntil` parameter is set to 1 hour from the time of call initiation
- DTMF timeout is set to 10 seconds (10000ms)
- Overall timeout for input capture is set to 20 seconds (20000ms)
- When responding to VCA webhooks, ensure the callflow format exactly matches the 8x8 API requirements 