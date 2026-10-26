"""
Automated Simulation Test Suite for AI Customer Support Email Workflow.
Executes all 7 test scenarios required by the Upwork client brief and validates assertions.
"""

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from simulator.fixtures import TEST_SCENARIOS
from simulator.pipeline_engine import SupportEmailPipeline
from simulator.mock_services import (
    MockPineconeVectorStore,
    MockOpenAIService,
    MockGmailThreadLedger
)


def run_full_suite() -> int:
    print("=" * 78)
    print("AI CUSTOMER SUPPORT EMAIL WORKFLOW - AUTOMATED VERIFICATION SUITE")
    print(f"Timestamp: 2026-10-26 | Target: n8n RAG Customer Support Automation")
    print("=" * 78)

    # Initialize shared pipeline state (shared ledger simulates realistic persistent inbox)
    shared_vector_store = MockPineconeVectorStore()
    shared_openai_service = MockOpenAIService()
    shared_gmail_ledger = MockGmailThreadLedger()

    pipeline = SupportEmailPipeline(
        vector_store=shared_vector_store,
        openai_service=shared_openai_service,
        gmail_ledger=shared_gmail_ledger,
        confidence_threshold=0.72
    )

    passed_count = 0
    failed_count = 0

    for idx, tc in enumerate(TEST_SCENARIOS, 1):
        s_id = tc["scenario_id"]
        s_name = tc["name"]
        print(f"\n[RUNNING {s_id}] {s_name}")
        print(f"  Description: {tc['description']}")
        print(f"  Sender: {tc['input_email']['sender_email']} | Subject: '{tc['input_email']['subject']}'")

        simulate_fault = tc.get("simulate_fault")
        result = pipeline.process_email(tc["input_email"], simulate_fault=simulate_fault)

        # Evaluate Scenario Assertions
        status = result["scenario_status"]
        print(f"  Result Route: -> {status}")

        try:
            if s_id == "TC_01":
                assert status == "AI_RESPONSE_GENERATION", f"Expected AI_RESPONSE_GENERATION, got {status}"
                assert result["reply_sent"] is True
                assert result["highest_score"] >= 0.75
                reply_body = result["reply_record"]["body"]
                for expected_phrase in tc["expected_result"]["reply_contains"]:
                    assert expected_phrase in reply_body, f"Missing '{expected_phrase}' in response body"
                assert result["reply_record"]["thread_id"] == "thread_alpha_101"
                assert result["reply_record"]["headers"]["In-Reply-To"] == tc["input_email"]["message_id"]

            elif s_id == "TC_02":
                assert status == "EXIT_CLEANLY_NO_REPLY", f"Expected EXIT_CLEANLY_NO_REPLY, got {status}"
                assert result["reply_sent"] is False
                assert result["classification"]["is_support_request"] is False

            elif s_id == "TC_03":
                assert status == "HUMAN_ESCALATION", f"Expected HUMAN_ESCALATION, got {status}"
                assert result["reply_sent"] is False
                assert result["escalated"] is True
                assert result["highest_score"] < 0.72
                assert "Needs-Human-Review" in shared_gmail_ledger.labeled_threads.get(tc["input_email"]["thread_id"], [])

            elif s_id == "TC_04":
                assert status == "AI_RESPONSE_GENERATION", f"Expected AI_RESPONSE_GENERATION, got {status}"
                assert result["reply_sent"] is True
                reply = result["reply_record"]
                assert reply["thread_id"] == "thread_alpha_101", "Thread ID mismatch!"
                assert reply["headers"]["In-Reply-To"] == tc["input_email"]["message_id"], "In-Reply-To header mismatch!"
                assert reply["headers"]["References"] == tc["input_email"]["message_id"], "References header mismatch!"

            elif s_id == "TC_05":
                assert status == "AI_RESPONSE_GENERATION", f"Expected AI_RESPONSE_GENERATION, got {status}"
                assert result["reply_sent"] is True
                reply_body = result["reply_record"]["body"]
                for expected_phrase in tc["expected_result"]["reply_contains"]:
                    assert expected_phrase in reply_body, f"Missing '{expected_phrase}' in response body"

            elif s_id == "TC_06":
                assert status == "ERROR_HANDLER", f"Expected ERROR_HANDLER, got {status}"
                assert "RateLimitError" in result["error"] or "HTTP 429" in result["error"]
                assert result["reply_sent"] is False

            elif s_id == "TC_07":
                assert status == "AI_RESPONSE_GENERATION", f"Expected AI_RESPONSE_GENERATION, got {status}"
                assert result["reply_sent"] is True
                reply_body = result["reply_record"]["body"]
                for expected_phrase in tc["expected_result"]["reply_contains"]:
                    assert expected_phrase in reply_body, f"Missing '{expected_phrase}' in response body"

            print(f"  [PASS] Assertion checks verified.")
            passed_count += 1

        except AssertionError as err:
            print(f"  [FAIL] Assertion failed: {err}")
            failed_count += 1

    print("\n" + "=" * 78)
    print(f"TEST SUMMARY: {passed_count} PASSED / {failed_count} FAILED out of {len(TEST_SCENARIOS)} scenarios.")
    print(f"Thread Ledger Status: {len(shared_gmail_ledger.sent_messages)} sent replies, {len(shared_gmail_ledger.escalated_threads)} escalated threads.")
    print("=" * 78)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(run_full_suite())
