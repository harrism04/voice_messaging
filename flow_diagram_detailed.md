```mermaid
%%{init: {
  'theme': 'base', 
  'themeVariables': {
    'primaryColor': '#BB2528',
    'primaryTextColor': '#fff',
    'primaryBorderColor': '#7C0000',
    'lineColor': '#F8B229',
    'secondaryColor': '#006100',
    'tertiaryColor': '#fff',
    'textColor': '#fff',
    'noteTextColor': '#333',
    'noteBkgColor': '#fff5ad',
    'edgeLabelBackground': 'rgba(0,0,0,0.5)',
    'background': 'transparent'
  }
}}%%
sequenceDiagram
    participant Provider as "Service Provider"
    participant LB as "Load Balancer"
    participant APISvc as "Integration Service"
    participant DB as "Database"
    participant Voice8x8 as "8x8 Voice API"
    participant Client as "Client Phone"
    rect rgb(100, 150, 220)
        note right of Provider: Appointment Confirmation Request
        Provider->>LB: POST /api/make-call
        Note over Provider,LB: Appointment data with 30-min trigger
        LB->>APISvc: Route request to service
        APISvc->>DB: Store appointment context
        APISvc->>Voice8x8: POST /api/v1/subaccounts/{id}/callflows
        Note over APISvc,Voice8x8: Configure makeCall and sayAndCapture actions
        
        Voice8x8->>Client: Initiate outbound call
        Note over Voice8x8,Client: 30 minutes before scheduled time
        Client->>Voice8x8: Answer call
        Voice8x8->>Client: Play voice message with details
        
        Voice8x8-->>APISvc: Async response with sessionId
        APISvc-->>DB: Update with sessionId and status
        APISvc-->>LB: Return confirmation response
        LB-->>Provider: 200 OK with operation status
    end
    rect rgb(100, 180, 120)
        note right of Voice8x8: DTMF Processing Flow
        Client->>Voice8x8: Press DTMF key (1=confirm, 0=cancel)
        Voice8x8->>LB: POST /api/webhooks/vca
        Note over Voice8x8,LB: Voice Call Action (VCA) webhook with DTMF data
        LB->>APISvc: Route webhook to service
        APISvc->>DB: Query appointment by sessionId
        APISvc->>DB: Update appointment status
        APISvc-->>LB: Return 200 OK
        LB-->>Voice8x8: Forward response
        Voice8x8->>Client: Play confirmation/cancellation message
        Voice8x8->>Voice8x8: Terminate call
    end
    rect rgb(200, 120, 120)
        note right of Voice8x8: Session Summary Processing
        Voice8x8->>LB: POST /api/webhooks/vss
        Note over Voice8x8,LB: Voice Session Summary (VSS) with call metrics
        LB->>APISvc: Route summary webhook
        APISvc->>DB: Retrieve appointment context
        APISvc->>DB: Persist call analytics
        APISvc->>Provider: POST webhook with final status
        Note over APISvc,Provider: Real-time appointment update
        APISvc-->>LB: Return 200 OK
        LB-->>Voice8x8: Forward acknowledgement
    end
```

## Flow Description

1. **Appointment Confirmation Request**
 - Service Provider sends call request with appointment details
 - Request routes through Load Balancer to Integration Service
 - Service stores appointment context in Database
 - Service configures call flow with 8x8 Voice API
 - 8x8 initiates outbound call 30 minutes before scheduled time
 - Client receives call with appointment details
 - Confirmation responses flow back through the system

2. **DTMF Processing Flow**
 - Client presses 1 (confirm) or 0 (cancel) on their phone
 - 8x8 Voice API sends VCA webhook with DTMF input
 - Request routes to Integration Service
 - Service updates appointment status in Database
 - Response flows back to 8x8 Voice API
 - Client hears confirmation/cancellation message
 - Call terminates

3. **Session Summary Processing**
 - Call ends with client
 - 8x8 Voice API sends Voice Session Summary with call metrics
 - Summary routes to Integration Service
 - Service retrieves context and persists call analytics
 - Service sends real-time update to Service Provider
 - System acknowledges receipt of summary
