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
    'textColor': 'var(--color-fg-default)',
    'noteTextColor': 'var(--color-fg-default)',
    'noteBkgColor': '#fff5ad',
    'noteTextColor': '#333',
    'edgeLabelBackground': '#fff',
    'background': 'transparent'
  }
}}%%
sequenceDiagram
    participant Platform as Restaurant Platform
    participant Middleware as Integration Middleware
    participant Voice8x8 as 8x8 Voice API
    participant Customer as Customer
    rect rgb(200, 220, 255)
        note right of Platform: 1. Reservation Confirmation (30 min before)
        Platform->>Middleware: Send reservation data
        Note over Platform,Middleware: Triggered 30 minutes before reservation time
        Middleware->>Voice8x8: POST callflows API request
        Voice8x8->>Customer: Initiate outbound call
        Customer->>Voice8x8: Answer call
        Voice8x8->>Customer: Play reservation details and prompt for input
    end
    rect rgb(220, 255, 220)
        note right of Customer: 2. Customer Response
        Customer->>Voice8x8: DTMF input (1=confirm, 0=cancel)
        Voice8x8->>Middleware: Webhook: customer response
        Middleware->>Platform: API call: update reservation status
        Voice8x8->>Customer: Play confirmation/cancellation message
    end
    rect rgb(255, 220, 220)
        note right of Voice8x8: 3. Call Summary
        Voice8x8->>Middleware: Webhook: session summary
        Middleware->>Platform: API call: final status update
        Note over Middleware,Platform: Complete call details and status
    end
```

## Flow Description

1. **Initial Make Call Request**
   - Client sends request to ngrok public URL
   - Ngrok forwards to local FastAPI server
   - FastAPI server calls 8x8 Voice API
   - Response flows back through the chain
   - 8x8 initiates phone call to customer

2. **VCA (Voice Call Action) Webhook**
   - Customer presses 1 (confirm) or 0 (cancel) on their phone
   - 8x8 Voice API sends DTMF input to ngrok URL
   - Request forwarded to FastAPI
   - FastAPI processes and returns next actions
   - Response flows back to 8x8 Voice API
   - Customer hears confirmation/cancellation message

3. **VSS (Voice Session Summary) Webhook**
   - Call ends with customer
   - 8x8 Voice API sends final call summary
   - Request forwarded through ngrok to FastAPI
   - FastAPI processes and acknowledges
   - Simple 200 OK response returned
