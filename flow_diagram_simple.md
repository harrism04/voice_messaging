# System Interaction Flow Diagram

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
    participant Provider as Service Provider
    participant Middleware as Integration Middleware
    participant Voice8x8 as 8x8 Voice API
    participant Client as Client
    rect rgb(100, 150, 220)
        note right of Provider: 1. Voice Message Delivery
        Provider->>Middleware: Send message data (OTP, notification, alert)
        Note over Provider,Middleware: Immediate delivery request
        Middleware->>Voice8x8: POST callflows makeCall API request
        Voice8x8->>Client: Initiate outbound call
        Client->>Voice8x8: Answer call
        Voice8x8->>Client: Play message via TTS (repeat N times)
        Voice8x8->>Voice8x8: Auto hangup after delivery
    end
    rect rgb(100, 180, 120)
        note right of Client: 2. Webhook Handling (Optional)
        Client->>Voice8x8: Any input (ignored)
        Voice8x8->>Middleware: Webhook: call event
        Middleware->>Voice8x8: Return hangup command
        Voice8x8->>Voice8x8: Terminate call immediately
    end
    rect rgb(200, 120, 120)
        note right of Voice8x8: 3. Call Summary
        Voice8x8->>Middleware: Webhook: session summary
        Middleware->>Provider: API call: delivery status update
        Note over Middleware,Provider: Complete call details and delivery status
    end
```

## Flow Description

1. **Initial Voice Message Request**
  - Client application sends message request to ngrok public URL
  - Ngrok forwards to local FastAPI server
  - FastAPI server calls 8x8 Voice API with message content
  - Response flows back through the chain
  - 8x8 initiates phone call to recipient
  - Message is delivered via text-to-speech (repeated N times)
  - Call automatically hangs up after message delivery

2. **VCA (Voice Call Action) Webhook**
  - If recipient provides any input during call (optional)
  - 8x8 Voice API sends call event to ngrok URL
  - Request forwarded to FastAPI
  - FastAPI processes and returns hangup command
  - Response flows back to 8x8 Voice API
  - Call terminates immediately

3. **VSS (Voice Session Summary) Webhook**
  - Call ends with recipient
  - 8x8 Voice API sends final call summary with delivery metrics
  - Request forwarded through ngrok to FastAPI
  - FastAPI processes delivery status and acknowledges
  - Simple 200 OK response returned
