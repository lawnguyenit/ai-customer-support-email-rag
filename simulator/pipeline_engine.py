"""
Reference Python Pipeline Engine for AI Customer Support Email Workflow.
Executes the identical node-by-node pipeline specification as the n8n production workflow.
"""

import re
from typing import Dict, Any, Optional
from simulator.mock_services import (
    MockPineconeVectorStore,
    MockOpenAIService,
    MockGmailThreadLedger
)


class SupportEmailPipeline:
    """Executes the customer support email RAG workflow node by node."""

    def __init__(
        self,
        vector_store: Optional[MockPineconeVectorStore] = None,
        openai_service: Optional[MockOpenAIService] = None,
        gmail_ledger: Optional[MockGmailThreadLedger] = None,
        confidence_threshold: float = 0.72
    ):
        self.vector_store = vector_store or MockPineconeVectorStore()
        self.openai_service = openai_service or MockOpenAIService()
        self.gmail_ledger = gmail_ledger or MockGmailThreadLedger()
        self.confidence_threshold = confidence_threshold

    def sanitize_input(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Node 02: Sanitizes incoming email data, strips Re:/Fwd:, cleans whitespace."""
        subject = email_data.get("subject", "").strip()
        clean_subject = re.sub(r"^(Re:\s*|Fwd:\s*)+", "", subject, flags=re.I).strip()
        body = email_data.get("body", "").strip()
        
        # Strip trailing signature or quoted thread if present
        clean_body = re.split(r"(?i)(^>|\nOn .* wrote:|\n---|\nBest regards|\nThanks,)", body)[0].strip()
        if not clean_body:
            clean_body = body

        return {
            "message_id": email_data["message_id"],
            "thread_id": email_data["thread_id"],
            "sender_email": email_data["sender_email"],
            "sender_name": email_data.get("sender_name", ""),
            "clean_subject": clean_subject,
            "clean_body": clean_body,
            "is_valid": len(clean_body) >= 3
        }

    def process_email(self, email_data: Dict[str, Any], simulate_fault: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes end-to-end pipeline.
        Returns a detailed execution record matching n8n execution telemetry.
        """
        audit_trail = []

        try:
            # Step 1: Intake & Sanitize
            sanitized = self.sanitize_input(email_data)
            audit_trail.append({"node": "node_01_intake", "status": "SUCCESS", "thread_id": sanitized["thread_id"]})
            audit_trail.append({"node": "node_02_sanitize", "status": "SUCCESS", "clean_subject": sanitized["clean_subject"]})

            # Step 2: AI Classification
            classification = self.openai_service.classify_email(
                subject=sanitized["clean_subject"],
                body=sanitized["clean_body"],
                simulate_fault=simulate_fault
            )
            audit_trail.append({
                "node": "node_03_classify",
                "status": "SUCCESS",
                "is_support": classification["is_support_request"],
                "category": classification["category"]
            })

            # Step 3: Support Filter Gate
            if not classification["is_support_request"]:
                audit_trail.append({
                    "node": "node_04_support_gate",
                    "status": "SKIPPED_NON_SUPPORT",
                    "action": "Clean exit without reply"
                })
                return {
                    "scenario_status": "EXIT_CLEANLY_NO_REPLY",
                    "audit_trail": audit_trail,
                    "classification": classification,
                    "reply_sent": False,
                    "escalated": False
                }

            # Step 4: Knowledge Retrieval (RAG via Pinecone)
            rag_result = self.vector_store.query(
                query_text=classification["core_query"],
                top_k=3
            )
            highest_score = rag_result["highest_score"]
            audit_trail.append({
                "node": "node_05_rag_query",
                "status": "SUCCESS",
                "matches_count": len(rag_result["matches"]),
                "highest_score": highest_score
            })

            # Step 5: Confidence Gate (Threshold Gating)
            if highest_score < self.confidence_threshold:
                # Route to Human Escalation Path
                escalation = self.gmail_ledger.escalate_thread(
                    thread_id=sanitized["thread_id"],
                    message_id=sanitized["message_id"],
                    sender_email=sanitized["sender_email"],
                    reason=f"Similarity score {highest_score} is below threshold {self.confidence_threshold}",
                    score=highest_score
                )
                audit_trail.append({
                    "node": "node_06_confidence_gate",
                    "status": "ROUTED_TO_ESCALATION",
                    "score": highest_score,
                    "threshold": self.confidence_threshold
                })
                audit_trail.append({
                    "node": "node_07b_human_escalation",
                    "status": "SUCCESS",
                    "label": "Needs-Human-Review",
                    "escalation_record": escalation
                })
                return {
                    "scenario_status": "HUMAN_ESCALATION",
                    "audit_trail": audit_trail,
                    "classification": classification,
                    "highest_score": highest_score,
                    "escalation": escalation,
                    "reply_sent": False,
                    "escalated": True
                }

            # Step 6: AI Response Generation
            response_text = self.openai_service.generate_response(
                customer_name=sanitized["sender_name"],
                inquiry=sanitized["clean_body"],
                context_docs=rag_result["matches"]
            )
            audit_trail.append({"node": "node_07a_generate_response", "status": "SUCCESS", "response_length": len(response_text)})

            # Step 7: Gmail Reply (Preserving Thread & RFC Headers)
            reply_record = self.gmail_ledger.send_reply(
                thread_id=sanitized["thread_id"],
                in_reply_to_message_id=sanitized["message_id"],
                to_email=sanitized["sender_email"],
                subject=sanitized["clean_subject"],
                body=response_text,
                labels=["AI-Answered"]
            )
            audit_trail.append({
                "node": "node_08a_gmail_reply",
                "status": "SUCCESS",
                "sent_message_id": reply_record["sent_message_id"],
                "thread_id": reply_record["thread_id"],
                "in_reply_to": reply_record["headers"]["In-Reply-To"]
            })

            return {
                "scenario_status": "AI_RESPONSE_GENERATION",
                "audit_trail": audit_trail,
                "classification": classification,
                "highest_score": highest_score,
                "reply_record": reply_record,
                "reply_sent": True,
                "escalated": False
            }

        except Exception as exc:
            # Step 8: Global Error Boundary
            audit_trail.append({
                "node": "node_error_handler",
                "status": "CAUGHT_EXCEPTION",
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            })
            return {
                "scenario_status": "ERROR_HANDLER",
                "audit_trail": audit_trail,
                "error": str(exc),
                "reply_sent": False,
                "escalated": False
            }
