# AI Customer Support Email Workflow (RAG, Pinecone, Gmail, OpenAI & Gemini)

**Project ID:** `portfolio-ai-customer-support-email-rag-2026-10-26`  
**Classification:** Portfolio Exercise & Enterprise Reusable Asset  
**Status:** **100% COMPLETE & VERIFIED** (7/7 Scenarios Passing + Live Google Gemini API Integration)  
**Execution Date:** 2026-10-26  

---

> [!TIP]
> **Tài liệu Showcase cho GitHub & Phỏng vấn tuyển dụng:**  
> Đọc ngay bản phân tích chuyên sâu tại 👉 **[`CASE_STUDY_PROBLEM_AND_SOLUTION.md`](CASE_STUDY_PROBLEM_AND_SOLUTION.md)**  
> *(Bao gồm: Bối cảnh khách hàng, Phân tích nghiệp vụ, 5 giải pháp kỹ thuật cụ thể trả lời cho câu hỏi "Tôi đã làm những gì trong project này?", Bằng chứng chạy thực tế với Google Gemini API, và Bộ câu hỏi phỏng vấn thực chiến).*

---

## 1. Project Overview

This project implements an end-to-end, production-ready **AI Customer Support Email Workflow** built in **n8n**, integrated with **Google Workspace (Gmail)**, **OpenAI (GPT-4o-mini & Embeddings)**, and **Pinecone Vector Database**.

It is engineered specifically to fulfill all technical, architectural, testing, and handover requirements outlined in the standard Upwork client brief for an *n8n AI Automation Specialist*.

### Key Capabilities
* **Dual-Stage Intent Triage:** Fast, low-latency classification via OpenAI JSON mode filters out spam, cold outreach, and marketing proposals before any vector query is billed.
* **Context-Grounded RAG:** Embeds customer queries (`text-embedding-3-small`, 1536 dims) and performs semantic vector search against a Pinecone knowledge index.
* **Strict Anti-Hallucination Gating:** Quantitative cosine similarity threshold (`>= 0.72`). Queries matching internal knowledge receive context-grounded AI replies; out-of-scope queries trigger human escalation without guessing.
* **RFC 2822 / 5322 Thread Continuity:** Preserves the Gmail `threadId` and maps `In-Reply-To` and `References` headers so replies stay collapsed within the original conversation.
* **Human-in-the-Loop Escalation:** Automatically tags low-confidence threads with `Needs-Human-Review` and dispatches alert webhooks with structured context to team channels.
* **Zero-Dependency Local Simulator:** A standalone test harness allowing 100% offline testing of all 7 edge scenarios in 0.002 seconds without requiring live API keys.

---

## 2. Deliverables Mandated by the Client Brief

All 5 core handover deliverables required by the client specification have been compiled and verified:

| Deliverable | File Path | Description |
| :--- | :--- | :--- |
| **1. Workflow Design & Integration Mapping** | [`docs/WORKFLOW_DESIGN_AND_INTEGRATION_MAPPING.md`](docs/WORKFLOW_DESIGN_AND_INTEGRATION_MAPPING.md) | Node-by-node architecture breakdown, I/O schemas, credential scopes, and security boundaries. |
| **2. Process Flow Diagram** | [`docs/PROCESS_FLOW_DIAGRAM.md`](docs/PROCESS_FLOW_DIAGRAM.md) | Visual Mermaid architecture diagram, sequence diagram, and RFC thread continuity mapping. |
| **3. Testing Notes & Validation Checklist** | [`docs/TESTING_NOTES_AND_VALIDATION_CHECKLIST.md`](docs/TESTING_NOTES_AND_VALIDATION_CHECKLIST.md) | Verification results across 7 required test scenarios (Support, Non-support, Missing KB, Threading, 429 Failures). |
| **4. Project Handover Summary** | [`docs/PROJECT_HANDOVER_SUMMARY.md`](docs/PROJECT_HANDOVER_SUMMARY.md) | Setup instructions, credential configuration (Gmail, OpenAI, Pinecone), activation steps, and runbook. |
| **5. Importable n8n Workflow JSON** | [`v1/ai-customer-support-email-rag.n8n.json`](v1/ai-customer-support-email-rag.n8n.json) | Ready-to-import n8n workflow file with 18 nodes, parameterized settings, and zero hardcoded secrets. |

---

## 3. Developer Knowledge Heritage & Reusable Framework

In addition to client deliverables, this directory contains reusable engineering assets designed to empower the freelancer across future client engagements:

* [`TUTORIAL.md`](TUTORIAL.md): **"Di sản tri thức: Cẩm nang xây dựng & Bán giải pháp AI Workflow trên Upwork"** — An in-depth guide covering the business value of this workflow, the 4 core technical pillars, adaptation patterns (Zendesk, Slack, Supabase), and a high-converting proposal template.
* [`DECISIONS.md`](DECISIONS.md): Architecture Decision Records (ADR) justifying why each design choice was made.
* [`JOB_SPEC.yaml`](JOB_SPEC.yaml) & [`PIPELINE.yaml`](PIPELINE.yaml): Formal contracts defining inputs, outputs, schemas, and acceptance criteria.
* [`simulator/`](simulator/): Complete offline test harness (`fixtures.py`, `mock_services.py`, `pipeline_engine.py`, `run_simulation.py`).
* [`tests/`](tests/): Standard library test suite executable anywhere via `python -m unittest`.
* [`VERIFICATION.md`](VERIFICATION.md): Audit log recording execution commands, outputs, and exit codes.

---

## 4. Quick Verification Command

Run the automated simulation suite locally:
```powershell
python D:\Project\Freelancer\Test\AI_Customer_Support_Email_n8n_RAG\2026-10-26\simulator\run_simulation.py
```
*Expected Result:*
```text
==============================================================================
TEST SUMMARY: 7 PASSED / 0 FAILED out of 7 scenarios.
Thread Ledger Status: 4 sent replies, 1 escalated threads.
==============================================================================
```
