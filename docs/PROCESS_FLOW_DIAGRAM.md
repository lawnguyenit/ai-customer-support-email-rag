# Deliverable 2: Process Flow Diagram

**Project:** AI Customer Support Email Workflow (n8n, Pinecone, OpenAI, Gmail)  
**Version:** 1.0.0  
**Date:** 2026-10-26  

---

## 1. High-Level Automation Architecture

The following flowchart illustrates the complete lifecycle of an incoming email through ingestion, classification, vector retrieval, confidence-gating, response generation, and escalation.

```mermaid
flowchart TD
    subgraph Intake ["Phase 1: Ingestion & Normalization"]
        A1["Incoming Email (Gmail Trigger)"] --> B["Sanitize & Normalize Email"]
        A2["Test Webhook (Simulator / Mock)"] --> B
        B --> C["Extract RFC Headers, Thread-ID & Clean Body"]
    end

    subgraph Triage ["Phase 2: Intent Classification Gate"]
        C --> D["OpenAI Intent Classifier (gpt-4o-mini)"]
        D --> E{"Is Support Request?"}
        E -- No (Spam / Cold Outreach) --> F["Non-Support Terminal (No-Op / Silent Drop)"]
        E -- Yes --> G["Generate Query Embedding (text-embedding-3-small)"]
    end

    subgraph RAG ["Phase 3: Knowledge Retrieval & Gating"]
        G --> H["Pinecone Vector Index (Top-K = 3)"]
        H --> I["Evaluate Max Similarity Score"]
        I --> J{"Similarity >= 0.72 ?"}
    end

    subgraph Execution ["Phase 4: Response or Escalation"]
        J -- Yes (Sufficient Knowledge) --> K["AI Response Generator (Context Grounded)"]
        K --> L["Gmail Reply (Preserving Thread & In-Reply-To)"]
        L --> M["Add 'AI-Answered' Label"]

        J -- No (Insufficient / Missing) --> N["Tag Gmail Thread ('Needs-Human-Review')"]
        N --> O["Dispatch Internal Webhook Alert (Slack / Discord)"]
    end

    subgraph ErrorHandling ["Phase 5: Global Safety Net"]
        P["Global Error Trigger"] --> Q["Log Incident & Notify Engineering Webhook"]
    end

    style F fill:#f9f9f9,stroke:#999,stroke-dasharray: 5 5
    style M fill:#d4edda,stroke:#28a745,stroke-width:2px
    style O fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style Q fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```

---

## 2. Sequence Diagram (Multi-Party Interaction)

This sequence diagram depicts the chronological message exchange between the Customer, Gmail Service, n8n Orchestrator, OpenAI, Pinecone Vector DB, and Agency Human Staff.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant Gmail as Gmail Workspace
    participant n8n as n8n Automation Engine
    participant OpenAI as OpenAI API
    participant Pinecone as Pinecone Vector DB
    actor Agent as Agency Support Agent

    Customer->>Gmail: Sends support email (Thread ID: #101)
    Gmail-->>n8n: Gmail Trigger (New Unread Message)
    
    rect rgb(240, 248, 255)
        note over n8n: Step 1: Sanitize & Classify
        n8n->>OpenAI: Classify intent (gpt-4o-mini)
        OpenAI-->>n8n: { is_support: true, query: "refund policy" }
    end

    rect rgb(245, 255, 245)
        note over n8n: Step 2: Vector Search & Confidence Evaluation
        n8n->>OpenAI: Generate embedding (1536 dims)
        OpenAI-->>n8n: Embedding vector
        n8n->>Pinecone: Query top-k docs with vector
        Pinecone-->>n8n: Matches (Best Score: 0.88, Doc: "14-day refund")
    end

    alt Confidence Score >= 0.72 (Automated Resolution)
        rect rgb(235, 250, 235)
            n8n->>OpenAI: Generate response strictly using context
            OpenAI-->>n8n: Grounded support draft
            n8n->>Gmail: Send Reply (threadId: #101, In-Reply-To: #msg-1)
            Gmail->>Customer: Delivers reply in same conversation thread
            n8n->>Gmail: Apply label "AI-Answered"
        end
    else Confidence Score < 0.72 (Human Escalation Path)
        rect rgb(255, 245, 235)
            n8n->>Gmail: Apply label "Needs-Human-Review"
            n8n->>Agent: Send Slack/Webhook alert with context & link
            Agent->>Gmail: Human reviews thread #101 and answers directly
        end
    end
```

---

## 3. RFC Thread Continuity Architecture

To guarantee that email replies stay grouped together inside the recipient's email software (Gmail, Outlook, Apple Mail), the workflow enforces the following header mappings:

```mermaid
classDiagram
    class IncomingEmail {
        +string messageId: "<msg-001@customer.org>"
        +string threadId: "18bb20f5a01"
        +string subject: "Order #88219"
        +string body: "Can I get a refund?"
    }

    class ReplyEmail {
        +string threadId: "18bb20f5a01"
        +string subject: "Re: Order #88219"
        +string InReplyTo: "<msg-001@customer.org>"
        +string References: "<msg-001@customer.org>"
        +string body: "Yes, you have 14 days..."
    }

    IncomingEmail <|-- ReplyEmail : Linked via Thread-ID & RFC 5322 In-Reply-To
```
