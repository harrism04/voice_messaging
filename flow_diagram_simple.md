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
        note right of Provider: 1. Appointment Confirmation (30 min before)
        Provider->>Middleware: Send appointment data
        Note over Provider,Middleware: Triggered 30 minutes before scheduled time
        Middleware->>Voice8x8: POST callflows makeCall API request
        Voice8x8->>Client: Initiate outbound call
        Client->>Voice8x8: Answer call
        Voice8x8->>Client: Play appointment details and prompt for input
    end
    rect rgb(100, 180, 120)
        note right of Client: 2. Client Response
        Client->>Voice8x8: DTMF input (1=confirm, 0=cancel)
        Voice8x8->>Middleware: Webhook: client response
        Middleware->>Provider: API call: update appointment status
        Voice8x8->>Client: Play confirmation/cancellation message
    end
    rect rgb(200, 120, 120)
        note right of Voice8x8: 3. Call Summary
        Voice8x8->>Middleware: Webhook: session summary
        Middleware->>Provider: API call: final status update
        Note over Middleware,Provider: Complete call details and status
    end
```

## Flow Description

1. **Initial Make Call Request**
  - Client application sends request to ngrok public URL
  - Ngrok forwards to local FastAPI server
  - FastAPI server calls 8x8 Voice API
  - Response flows back through the chain
  - 8x8 initiates phone call to recipient

2. **VCA (Voice Call Action) Webhook**
  - Recipient presses 1 (confirm) or 0 (cancel) on their phone
  - 8x8 Voice API sends DTMF input to ngrok URL
  - Request forwarded to FastAPI
  - FastAPI processes and returns next actions
  - Response flows back to 8x8 Voice API
  - Recipient hears confirmation/cancellation message

3. **VSS (Voice Session Summary) Webhook**
  - Call ends with recipient
  - 8x8 Voice API sends final call summary
  - Request forwarded through ngrok to FastAPI
  - FastAPI processes and acknowledges
  - Simple 200 OK response returned
