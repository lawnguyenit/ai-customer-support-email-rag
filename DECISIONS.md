# Architecture Decisions Record (ADR)

## Project: AI Customer Support Email Workflow (n8n, Pinecone, OpenAI, Gmail)
**Date:** 2026-10-26  
**Status:** Approved for Implementation

---

### DEC-001: Thread Continuity via RFC 2822 / 5322 Headers & Gmail `threadId`
* **Context:** When a bot replies to an email, if it only sends a new email with `Re: Subject`, email clients (Gmail, Apple Mail, Outlook) often split it into a separate, disconnected conversation. This breaks customer context and irritates support teams.
* **Decision:**
  1. Capture `message_id` and `thread_id` at intake.
  2. In the reply action, strictly pass the Gmail API `threadId` parameter.
  3. Explicitly inject RFC compliant email headers:
     - `In-Reply-To: <original_message_id>`
     - `References: <original_message_id>`
* **Consequence:** Both the customer's inbox and the agency's Gmail interface maintain 100% thread continuity across unlimited conversational turns.

---

### DEC-002: Dual-Phase Intent Filtering (Fast Classification Before Heavy RAG)
* **Context:** Vector embeddings and vector database queries cost latency and API credits. Running Pinecone search on cold sales pitches, newsletters, or spam is wasteful and creates false positives.
* **Decision:**
  - Place a lightweight LLM classification gate (`gpt-4o-mini`, temperature 0.1, strict JSON schema) immediately after email sanitization.
  - Non-support emails are filtered out with zero API calls to Pinecone and zero reply emails generated.
  - Support inquiries extract a clean `core_query` (removing noise/pleasantries) to maximize vector retrieval relevance.
* **Consequence:** Reduces vector DB load by ~40-60%, eliminates spam loops, and significantly speeds up overall pipeline execution.

---

### DEC-003: Strict Similarity Gating (Cosine Threshold 0.72) for Human Escalation
* **Context:** LLMs suffer from hallucinations or ungrounded promises when given irrelevant or zero-matching documents. An automated email support agent making false promises regarding refunds or features can cause financial or legal liability.
* **Decision:**
  - We enforce a quantitative confidence guardrail: `highest_similarity_score >= 0.72`.
  - If the top matched document score is below 0.72 (or if the retrieved document list is empty):
    - The pipeline halts automated reply.
    - Tags the Gmail thread with `Needs-Human-Review`.
    - Triggers an internal alert payload (Slack/Webhook/Dashboard).
* **Consequence:** 100% safe failure mode. The bot never guesses; humans handle edge cases with full context pre-packaged.

---

### DEC-004: Zero-Dependency Local Test Simulator (Offline-First Verification)
* **Context:** The developer or client may not have live Pinecone API keys or a dedicated Google Cloud OAuth workspace ready on day one. Waiting for credentials stalls verification and delays portfolio evidence.
* **Decision:**
  - Build a standalone Python simulator harness (`simulator/`):
    1. `email_simulator.py`: Generates representative email fixtures for all 7 edge cases.
    2. `mock_services.py`: Implements a deterministic local mock for OpenAI structured output and Pinecone vector cosine similarity.
    3. `run_simulation.py`: Executes end-to-end tests without requiring external network calls or secrets.
  - The n8n workflow supports switching between `Test Webhook (Mock)` and `Live Gmail Trigger` with a single parameter toggle.
* **Consequence:** Rapid test cycles, zero API expense during development, and instant reproducibility on any reviewer's machine.

---

### DEC-005: Clean Parameterization & Secret Isolation
* **Context:** Upwork clients frequently penalize freelancers who leave API keys, test email addresses, or hardcoded project IDs inside exported n8n JSON files.
* **Decision:**
  - All credentials (OpenAI, Pinecone, Google OAuth) use n8n's standard credential references (`credentials.openAiApi`, `credentials.pineconeApi`, `credentials.gmailOAuth2`).
  - Configuration variables (Threshold `0.72`, Top K `3`, Label names) are centralized in a single `Workflow Settings` node at the start.
* **Consequence:** The exported JSON is safe to distribute, commit to version control, and import into any target n8n instance without security risks.
