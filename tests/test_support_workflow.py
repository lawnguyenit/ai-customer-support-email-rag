"""
Unit and Integration Tests for AI Customer Support Email Workflow
Uses standard library unittest for universal execution without external dependencies.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.fixtures import TEST_SCENARIOS, KNOWLEDGE_BASE_ARTICLES
from simulator.pipeline_engine import SupportEmailPipeline
from simulator.mock_services import (
    MockPineconeVectorStore,
    MockOpenAIService,
    MockGmailThreadLedger
)


class TestSupportEmailWorkflow(unittest.TestCase):

    def setUp(self):
        self.vector_store = MockPineconeVectorStore(KNOWLEDGE_BASE_ARTICLES)
        self.openai_service = MockOpenAIService()
        self.gmail_ledger = MockGmailThreadLedger()
        self.pipeline = SupportEmailPipeline(
            vector_store=self.vector_store,
            openai_service=self.openai_service,
            gmail_ledger=self.gmail_ledger,
            confidence_threshold=0.72
        )

    def test_tc01_support_refund_request(self):
        """TC_01: Support inquiry on refund within 14 days should generate AI reply preserving thread."""
        tc = TEST_SCENARIOS[0]
        res = self.pipeline.process_email(tc["input_email"])

        self.assertEqual(res["scenario_status"], "AI_RESPONSE_GENERATION")
        self.assertTrue(res["reply_sent"])
        self.assertFalse(res["escalated"])
        self.assertGreaterEqual(res["highest_score"], 0.75)

        reply = res["reply_record"]
        self.assertEqual(reply["thread_id"], "thread_alpha_101")
        self.assertEqual(reply["headers"]["In-Reply-To"], "<msg-20261026-001@customer.org>")
        self.assertIn("14 days", reply["body"])
        self.assertIn("3 to 5 business days", reply["body"])

    def test_tc02_non_support_cold_outreach(self):
        """TC_02: Spam/cold sales pitch must be silently dropped without sending reply."""
        tc = TEST_SCENARIOS[1]
        res = self.pipeline.process_email(tc["input_email"])

        self.assertEqual(res["scenario_status"], "EXIT_CLEANLY_NO_REPLY")
        self.assertFalse(res["reply_sent"])
        self.assertFalse(res["classification"]["is_support_request"])
        self.assertEqual(len(self.gmail_ledger.sent_messages), 0)

    def test_tc03_insufficient_knowledge_escalation(self):
        """TC_03: Obscure hardware module query must route to human escalation with tag."""
        tc = TEST_SCENARIOS[2]
        res = self.pipeline.process_email(tc["input_email"])

        self.assertEqual(res["scenario_status"], "HUMAN_ESCALATION")
        self.assertFalse(res["reply_sent"])
        self.assertTrue(res["escalated"])
        self.assertLess(res["highest_score"], 0.72)

        # Check tag in ledger
        labels = self.gmail_ledger.labeled_threads.get("thread_escalate_303", [])
        self.assertIn("Needs-Human-Review", labels)

    def test_tc04_multi_turn_thread_continuity(self):
        """TC_04: Second message on same thread must retain threadId and RFC headers."""
        tc = TEST_SCENARIOS[3]
        res = self.pipeline.process_email(tc["input_email"])

        self.assertEqual(res["scenario_status"], "AI_RESPONSE_GENERATION")
        reply = res["reply_record"]
        self.assertEqual(reply["thread_id"], "thread_alpha_101")
        self.assertEqual(reply["headers"]["In-Reply-To"], "<msg-followup-404@customer.org>")
        self.assertEqual(reply["headers"]["References"], "<msg-followup-404@customer.org>")

    def test_tc05_account_access_password_reset(self):
        """TC_05: Password reset inquiry must return grounded URL and validity window."""
        tc = TEST_SCENARIOS[4]
        res = self.pipeline.process_email(tc["input_email"])

        self.assertEqual(res["scenario_status"], "AI_RESPONSE_GENERATION")
        self.assertIn("forgot-password", res["reply_record"]["body"])
        self.assertIn("30 minutes", res["reply_record"]["body"])

    def test_tc06_integration_fault_rate_limit(self):
        """TC_06: Simulated 429 rate limit must be caught by error boundary."""
        tc = TEST_SCENARIOS[5]
        res = self.pipeline.process_email(tc["input_email"], simulate_fault="OPENAI_429_RATE_LIMIT")

        self.assertEqual(res["scenario_status"], "ERROR_HANDLER")
        self.assertIn("RateLimitError", res["error"])
        self.assertFalse(res["reply_sent"])

    def test_tc07_api_quota_rate_limits(self):
        """TC_07: Developer query on rate limits must retrieve 60 req/min limits."""
        tc = TEST_SCENARIOS[6]
        res = self.pipeline.process_email(tc["input_email"])

        self.assertEqual(res["scenario_status"], "AI_RESPONSE_GENERATION")
        self.assertIn("60 requests per minute", res["reply_record"]["body"])


if __name__ == "__main__":
    unittest.main()
