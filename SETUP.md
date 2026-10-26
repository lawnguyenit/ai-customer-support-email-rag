# Local Setup & Verification Guide

This guide describes how to run and verify the **AI Customer Support Email Workflow** project locally on your development machine.

---

## 1. Quick Offline Verification (0 Credentials Required)

The project includes a standalone simulator that executes the complete pipeline without requiring live Google, OpenAI, or Pinecone accounts.

### Run the Simulation Test Suite
```powershell
python D:\Project\Freelancer\Test\AI_Customer_Support_Email_n8n_RAG\2026-10-26\simulator\run_simulation.py
```

### Run the Unit Tests
```powershell
python -m unittest discover -s D:\Project\Freelancer\Test\AI_Customer_Support_Email_n8n_RAG\2026-10-26\tests
```

Both commands will execute all 7 edge scenarios in under 1 second and report assertion verification.

---

## 2. Running in Local n8n Instance

If you have a local n8n instance running via Docker or npm:

1. Launch n8n:
   ```powershell
   n8n start
   # or with docker:
   # docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
   ```
2. Open `http://localhost:5678`.
3. In the Workflows menu, click **Import from File** and select:
   `D:\Project\Freelancer\Test\AI_Customer_Support_Email_n8n_RAG\2026-10-26\v1\ai-customer-support-email-rag.n8n.json`.
4. You can immediately trigger test runs via the `Test Webhook (Offline & Simulator Ingest)` node by posting JSON payloads.

---

## 3. Directory Layout

```text
2026-10-26/
├── DECISIONS.md            # Architecture Decision Records (ADR)
├── JOB_SPEC.yaml           # Client brief, scope boundaries, acceptance criteria
├── PIPELINE.yaml           # Node-by-node schema contracts and parameters
├── README.md               # Project overview and executive summary
├── SETUP.md                # This setup guide
├── TASKS.yaml              # Milestone and task tracking
├── TUTORIAL.md             # Reusable framework & client pitch guide
├── VERIFICATION.md         # Automated test logs and audit proof
├── docs/                   # 4 Core Handover Deliverables mandated by brief
│   ├── PROCESS_FLOW_DIAGRAM.md
│   ├── PROJECT_HANDOVER_SUMMARY.md
│   ├── TESTING_NOTES_AND_VALIDATION_CHECKLIST.md
│   └── WORKFLOW_DESIGN_AND_INTEGRATION_MAPPING.md
├── simulator/              # Offline test harness and mock services
│   ├── fixtures.py
│   ├── mock_services.py
│   ├── pipeline_engine.py
│   └── run_simulation.py
├── tests/                  # Standard library test suite
│   └── test_support_workflow.py
└── v1/                     # Final Deliverable 5
    └── ai-customer-support-email-rag.n8n.json
```
