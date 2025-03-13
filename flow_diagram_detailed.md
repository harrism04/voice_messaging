sequenceDiagram
    participant ResPlatform as "Restaurant Platform"
    participant LB as "Load Balancer"
    participant APISvc as "Integration Service"
    participant DB as "Database"
    participant Voice8x8 as "8x8 Voice API"
    participant Customer as "Customer Phone"

    rect rgb(200, 220, 255)
        note right of ResPlatform: Reservation Confirmation Request
        ResPlatform->>LB: POST /api/make-call
        Note over ResPlatform,LB: Reservation data with 30-min trigger
        LB->>APISvc: Route request to service
        APISvc->>DB: Store reservation context
        APISvc->>Voice8x8: POST /api/v1/subaccounts/{id}/callflows
        Note over APISvc,Voice8x8: Configure makeCall and sayAndCapture actions
        
        Voice8x8->>Customer: Initiate outbound call
        Note over Voice8x8,Customer: 30 minutes before reservation time
        Customer->>Voice8x8: Answer call
        Voice8x8->>Customer: Play voice message with details
        
        Voice8x8-->>APISvc: Async response with sessionId
        APISvc-->>DB: Update with sessionId and status
        APISvc-->>LB: Return confirmation response
        LB-->>ResPlatform: 200 OK with operation status
    end

    rect rgb(220, 255, 220)
        note right of Voice8x8: DTMF Processing Flow
        Customer->>Voice8x8: Press DTMF key (1=confirm, 0=cancel)
        Voice8x8->>LB: POST /api/webhooks/vca
        Note over Voice8x8,LB: Voice Call Action (VCA) webhook with DTMF data
        LB->>APISvc: Route webhook to service
        APISvc->>DB: Query reservation by sessionId
        APISvc->>DB: Update reservation status
        APISvc-->>LB: Return 200 OK
        LB-->>Voice8x8: Forward response
        Voice8x8->>Customer: Play confirmation/cancellation message
        Voice8x8->>Voice8x8: Terminate call
    end

    rect rgb(255, 220, 220)
        note right of Voice8x8: Session Summary Processing
        Voice8x8->>LB: POST /api/webhooks/vss
        Note over Voice8x8,LB: Voice Session Summary (VSS) with call metrics
        LB->>APISvc: Route summary webhook
        APISvc->>DB: Retrieve reservation context
        APISvc->>DB: Persist call analytics
        APISvc->>ResPlatform: POST webhook with final status
        Note over APISvc,ResPlatform: Real-time reservation update
        APISvc-->>LB: Return 200 OK
        LB-->>Voice8x8: Forward acknowledgement
    end
