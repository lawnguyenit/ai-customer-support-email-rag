# Deliverable 1: Workflow Design & Integration Mapping

**Project:** AI Customer Support Email Workflow (n8n, Pinecone, OpenAI, Gmail)  
**Version:** 1.0.0  
**Author:** AI Automation Engineering Team  
**Date:** 2026-10-26  

---

## 1. Executive Architecture Summary

The workflow provides autonomous, context-grounded email customer support triage and response for agency operations. It enforces strict anti-hallucination guardrails via a two-tier filter:
1. **Intent Classification:** Drops non-support inquiries (cold pitches, spam) without consuming vector tokens or sending unwanted replies.
2. **Confidence-Gated RAG:** Vector retrieval against Pinecone with an enforced similarity threshold (`0.72`). Queries matching known knowledge receive an immediate, professional, context-grounded AI reply. Queries below the threshold or outside knowledge scope are automatically escalated to human agents with metadata and thread tags.

---

## 2. End-to-End Node Specification Table

| Node ID | Node Name | Type | Key Responsibility & Inputs | Outputs & Downstream Routing |
| :--- | :--- | :--- | :--- | :--- |
| `01` | **Workflow Settings & Thresholds** | `n8n-nodes-base.set` | Central config: `CONFIDENCE_THRESHOLD: 0.72`, `VECTOR_TOP_K: 3`, `SUPPORT_LABEL`, `ESCALATION_LABEL`, `PINECONE_INDEX_HOST`. | Passes global parameters to all downstream nodes. |
| `02A` | **Gmail Trigger (New Incoming Email)** | `n8n-nodes-base.gmailTrigger` | Polls inbox for unread support emails. Captures `id`, `threadId`, `from`, `subject`, `text`, `html`. | Routes to Node `03` (Sanitize & Normalize). |
| `02B` | **Test Webhook (Offline & Simulator)** | `n8n-nodes-base.webhook` | Receives synthetic JSON payload (`/webhook/test-support-email`) for local development without live Google credentials. | Routes to Node `03` (Sanitize & Normalize). |
| `03` | **Sanitize & Normalize Email** | `n8n-nodes-base.code` | Normalizes subject (strips `Re:`, `Fwd:`), extracts clean body (strips quoted historical email chains and signatures), normalizes sender name and RFC identifiers. | `{ message_id, thread_id, sender_email, sender_name, clean_subject, clean_body, received_at }` |
| `04` | **OpenAI Intent Classifier** | `n8n-nodes-base.httpRequest` | Calls OpenAI `gpt-4o-mini` with JSON mode to classify email into support vs non-support, category, urgency, and extracts distilled `core_query`. | Structured JSON classification payload. |
| `05` | **Parse Classification** | `n8n-nodes-base.code` | Merges classification object back with email identifiers and safeguards fallback values in case of schema discrepancy. | Merged normalized record with `classification` object. |
| `06` | **Is Support Request?** | `n8n-nodes-base.if` | Evaluates `$json.classification.is_support_request == true`. | **True:** Node `08` (Embedding)<br>**False:** Node `07` (Non-Support Terminal). |
| `07` | **Non-Support Clean Exit** | `n8n-nodes-base.noOp` | Terminal sink for cold sales outreach, spam, or autoresponders. No reply is generated. Execution completes cleanly. | End of pipeline (0 cost, 0 noise). |
| `08` | **Generate Query Embedding** | `n8n-nodes-base.httpRequest` | Sends `classification.core_query` to OpenAI `text-embedding-3-small` (1536 dims). | Raw 1536-dimensional vector float array. |
| `09` | **Pinecone Vector Query (RAG)** | `n8n-nodes-base.httpRequest` | Queries Pinecone index host (`/query`) with vector, `topK: 3`, and `includeMetadata: true`. | Matches array with document metadata and similarity scores. |
| `10` | **Evaluate Similarity & Gating** | `n8n-nodes-base.code` | Compares highest cosine similarity score against `CONFIDENCE_THRESHOLD` (0.72). Extracts relevant text chunks. | Sets `is_knowledge_sufficient: boolean`, `highest_similarity_score: float`. |
| `11` | **Sufficient Knowledge?** | `n8n-nodes-base.if` | Binary router checking `$json.is_knowledge_sufficient == true`. | **True:** Node `12A` (AI Response Gen)<br>**False:** Node `12B` (Escalation). |
| `12A` | **AI Response Generator (RAG)** | `n8n-nodes-base.httpRequest` | Prompts `gpt-4o-mini` with strict system constraints. Grounded strictly on retrieved knowledge snippets. Formats professional response. | AI drafted response text. |
| `13A` | **Gmail Reply (Preserving Thread)** | `n8n-nodes-base.gmail` | Sends reply using Gmail API with `threadId`, `In-Reply-To`, and `References` headers. Adds `AI-Answered` label. | Verified thread reply delivered to customer. |
| `12B` | **Tag Gmail Thread (Needs-Human-Review)** | `n8n-nodes-base.gmail` | Injects `Needs-Human-Review` label onto the Gmail thread so agency staff see it immediately. | Thread tagged in inbox. |
| `13B` | **Dispatch Escalation Webhook / Alert** | `n8n-nodes-base.httpRequest` | Sends alert to Slack / Discord / Webhook with customer details, inquiry snippet, similarity score, and direct link. | Human agent notified with complete context. |
| `14` | **Global Error Boundary** | `n8n-nodes-base.errorTrigger` | Traps any unhandled runtime error (rate limit, network timeout, authentication drop). | Triggers Node `15`. |
| `15` | **Notify Incident Channel** | `n8n-nodes-base.httpRequest` | Posts incident diagnostics to internal alert webhook without exposing error details to customers. | Engineering incident recorded. |

---

## 3. Integration & Credential Mapping

### 3.1. Google Workspace / Gmail Integration
* **Credential Type:** `gmailOAuth2`
* **OAuth Scopes Required:**
  * `https://www.googleapis.com/auth/gmail.modify` (Read unread emails, send replies, apply labels)
  * `https://www.googleapis.com/auth/gmail.labels` (List and create labels)
* **Thread Continuity Mapping:**
  ```json
  {
    "threadId": "={{ $json.thread_id }}",
    "inReplyTo": "={{ $json.message_id }}",
    "references": "={{ $json.message_id }}"
  }
  ```
  *Note:* By supplying both `threadId` in the API call and `In-Reply-To` / `References` in RFC 5322 headers, the response is guaranteed to stay within the existing thread on all email clients.

### 3.2. OpenAI API Integration
* **Credential Type:** `httpHeaderAuth`
* **Header:** `Authorization: Bearer <OPENAI_API_KEY>`
* **Endpoints Used:**
  * `/v1/chat/completions` (Classifier: `gpt-4o-mini`, JSON mode; Generator: `gpt-4o-mini`, temperature 0.2)
  * `/v1/embeddings` (Embedding Model: `text-embedding-3-small`, 1536 dimensions)

### 3.3. Pinecone Vector Database Integration
* **Credential Type:** `httpHeaderAuth`
* **Header:** `Api-Key: <PINECONE_API_KEY>`
* **Target Index Host:** Configurable via `PINECONE_INDEX_HOST` setting (e.g. `https://customer-support-kb-<id>.svc.<region>.pinecone.io`)
* **Endpoint Used:** `POST /query`
* **Payload Specification:**
  ```json
  {
    "vector": [0.0123, -0.0456, "... (1536 floats)"],
    "topK": 3,
    "includeMetadata": true
  }
  ```

---

## 4. Guardrails & Anti-Hallucination Design

1. **Prompt Grounding Constraint:** The AI Response Generator system prompt explicitly forbids speculation. If a detail is missing from the retrieved context, the prompt instructs the model to omit it rather than fabricate dates, pricing, or technical claims.
2. **Deterministic Confidence Gate:** Regardless of what the LLM might hallucinate, if the Pinecone cosine similarity score is below `0.72`, the workflow hard-stops the automated reply path and redirects to human triage.
3. **Loop Prevention:** Non-support emails, automated delivery failure notices (DSN), and existing bot responses are flagged during sanitization to avoid automated infinite email loops.
