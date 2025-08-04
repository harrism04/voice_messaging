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
        note right of Provider: Voice Message Delivery Request
        Provider->>LB: POST /api/make-call
        Note over Provider,LB: Message data (OTP, notification, alert)
        LB->>APISvc: Route request to service
        APISvc->>DB: Store message context
        APISvc->>Voice8x8: POST /api/v1/subaccounts/{id}/callflows
        Note over APISvc,Voice8x8: Configure makeCall, say, and hangup actions
        
        Voice8x8->>Client: Initiate outbound call
        Note over Voice8x8,Client: Immediate delivery
        Client->>Voice8x8: Answer call
        Voice8x8->>Client: Play message via TTS (repeat N times)
        Voice8x8->>Voice8x8: Auto hangup after message delivery
        
        Voice8x8-->>APISvc: Async response with sessionId
        APISvc-->>DB: Update with sessionId and status
        APISvc-->>LB: Return confirmation response
        LB-->>Provider: 200 OK with operation status
    end
    rect rgb(100, 180, 120)
        note right of Voice8x8: Webhook Processing Flow
        Voice8x8->>LB: POST /api/webhooks/vca
        Note over Voice8x8,LB: Voice Call Action (VCA) webhook (any input)
        LB->>APISvc: Route webhook to service
        APISvc->>DB: Query message by sessionId
        APISvc->>DB: Update message status
        APISvc-->>LB: Return hangup response
        LB-->>Voice8x8: Forward hangup command
        Voice8x8->>Voice8x8: Terminate call immediately
    end
    rect rgb(200, 120, 120)
        note right of Voice8x8: Session Summary Processing
        Voice8x8->>LB: POST /api/webhooks/vss
        Note over Voice8x8,LB: Voice Session Summary (VSS) with call metrics
        LB->>APISvc: Route summary webhook
        APISvc->>DB: Retrieve message context
        APISvc->>DB: Persist call analytics
        APISvc->>Provider: POST webhook with final status
        Note over APISvc,Provider: Real-time delivery status update
        APISvc-->>LB: Return 200 OK
        LB-->>Voice8x8: Forward acknowledgement
    end
```

## Flow Description

1. **Voice Message Delivery Request**
 - Service Provider sends call request with message content (OTP, notification, alert)
 - Request routes through Load Balancer to Integration Service
 - Service stores message context in Database
 - Service configures call flow with 8x8 Voice API (makeCall + say + hangup)
 - 8x8 initiates outbound call for immediate delivery
 - Client receives call and hears message via text-to-speech
 - Call automatically hangs up after message delivery (repeated N times)
 - Confirmation responses flow back through the system

2. **Webhook Processing Flow**
 - 8x8 Voice API sends VCA webhook for any call events or input
 - Request routes to Integration Service via Load Balancer
 - Service updates message delivery status in Database
 - Service responds with hangup command for any input
 - Response flows back to 8x8 Voice API
 - Call terminates immediately on any client input

3. **Session Summary Processing**
 - Call ends with client
 - 8x8 Voice API sends Voice Session Summary with call metrics
 - Summary routes to Integration Service
 - Service retrieves context and persists call analytics
 - Service sends real-time delivery status update to Service Provider
 - System acknowledges receipt of summary
