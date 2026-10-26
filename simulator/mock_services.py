"""
Deterministic Mock Services for Pinecone Vector Search, OpenAI LLM, and Gmail Thread Ledger.
Enables 100% offline testing of the RAG customer support pipeline without API keys.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from simulator.fixtures import KNOWLEDGE_BASE_ARTICLES


class MockPineconeVectorStore:
    """Simulates Pinecone vector database index with cosine similarity scoring."""

    def __init__(self, articles: Optional[List[Dict[str, Any]]] = None):
        self.articles = articles or KNOWLEDGE_BASE_ARTICLES

    def _calculate_mock_similarity(self, query: str, article: Dict[str, Any]) -> float:
        """
        Calculates a deterministic similarity score (0.0 to 1.0) based on
        keyword matching and token overlap to simulate embedding cosine distance.
        """
        query_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
        if not query_words:
            return 0.0

        article_text = (article["title"] + " " + article["text"]).lower()
        article_words = set(re.findall(r"\b\w{3,}\b", article_text))
        keywords = set(k.lower() for k in article.get("keywords", []))

        # Check keyword hits
        keyword_hits = 0
        for kw in keywords:
            if kw in query.lower():
                keyword_hits += 1

        # Check word overlap
        overlap = len(query_words.intersection(article_words))
        overlap_ratio = overlap / len(query_words)

        # Base score synthesized from keyword presence and word overlap
        base_score = (overlap_ratio * 0.5) + (min(keyword_hits, 3) * 0.18)

        # Specific domain boost if matching category
        if any(w in query.lower() for w in ["refund", "cancel", "money back"]) and article["category"] == "billing_refund":
            base_score = max(base_score, 0.88)
        elif any(w in query.lower() for w in ["password", "login", "locked out"]) and article["category"] == "account_access":
            base_score = max(base_score, 0.86)
        elif any(w in query.lower() for w in ["429", "rate limit", "quota"]) and article["category"] == "technical_issue":
            base_score = max(base_score, 0.91)
        elif any(w in query.lower() for w in ["quantum", "hsm", "lattice"]):
            base_score = min(base_score, 0.35)  # Intentionally low for out-of-scope query

        return min(max(round(base_score, 4), 0.1), 0.98)

    def query(self, query_text: str, top_k: int = 3) -> Dict[str, Any]:
        """Queries the mock vector database and returns top-k matching documents."""
        scored_docs = []
        for doc in self.articles:
            score = self._calculate_mock_similarity(query_text, doc)
            scored_docs.append({
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "category": doc["category"],
                "score": score
            })

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        top_matches = scored_docs[:top_k]
        highest_score = top_matches[0]["score"] if top_matches else 0.0

        return {
            "query": query_text,
            "matches": top_matches,
            "highest_score": highest_score
        }


class MockOpenAIService:
    """Simulates OpenAI LLM structured classification and context-grounded response generation."""

    def classify_email(self, subject: str, body: str, simulate_fault: Optional[str] = None) -> Dict[str, Any]:
        """Simulates structured intent classification using gpt-4o-mini."""
        if simulate_fault == "OPENAI_429_RATE_LIMIT":
            raise RuntimeError("HTTP 429: OpenAI RateLimitError - Rate limit reached for requests.")

        full_text = (subject + " " + body).lower()

        # Check for non-support signals (spam, cold outreach, marketing)
        spam_indicators = ["seo traffic", "backlinks", "quick call", "growth", "10x", "rank #1", "pitch"]
        if any(ind in full_text for ind in spam_indicators):
            return {
                "is_support_request": False,
                "category": "non_support",
                "urgency": "low",
                "sentiment": "neutral",
                "core_query": "Cold sales pitch / unsolicited marketing proposal"
            }

        # Check categories
        if any(w in full_text for w in ["refund", "billing", "money back", "cancel"]):
            cat = "billing_refund"
            urgency = "medium"
        elif any(w in full_text for w in ["password", "login", "locked out", "mfa", "token"]):
            cat = "account_access"
            urgency = "high"
        elif any(w in full_text for w in ["429", "rate limit", "error", "down", "bug", "hsm", "quantum"]):
            cat = "technical_issue"
            urgency = "high" if "down" in full_text else "medium"
        else:
            cat = "general_inquiry"
            urgency = "low"

        # Core query distillation: combine distilled subject and body intent
        core_query = f"{subject}. {body}"

        return {
            "is_support_request": True,
            "category": cat,
            "urgency": urgency,
            "sentiment": "frustrated" if urgency == "high" else "neutral",
            "core_query": core_query
        }

    def generate_response(self, customer_name: str, inquiry: str, context_docs: List[Dict[str, Any]]) -> str:
        """Simulates response generation grounded in retrieved knowledge base articles."""
        name = customer_name or "Valued Customer"
        best_doc = context_docs[0] if context_docs else None
        top_text = best_doc["text"] if best_doc else ""

        # Context-grounded synthesis based on top matching document
        points = []
        if "14 days" in top_text:
            points.append("You are eligible for a 100% full refund within 14 days of your purchase.")
            points.append("Please forward your order ID to billing@agency.com to initiate the refund.")
            points.append("Once submitted, refunds are processed back to your original payment method within 3 to 5 business days.")
        elif "forgot-password" in top_text:
            points.append("You can reset your account password by visiting https://app.agency.com/forgot-password.")
            points.append("Please note that password reset tokens remain valid for 30 minutes from generation.")
            points.append("If you have lost access to your 2FA/MFA token, an administrator can provide a temporary recovery code.")
        elif "60 requests per minute" in top_text:
            points.append("Standard plan accounts are allotted up to 60 requests per minute and 10,000 requests per day.")
            points.append("When rate limits are exceeded, the API responds with HTTP 429 along with a Retry-After header.")
            points.append("For higher throughput (up to 600 requests per minute), our Enterprise tier is available.")
        else:
            points.append("Thank you for reaching out to customer support. We have received your query regarding: " + inquiry[:60] + "...")

        formatted_points = "\n".join(f"- {p}" for p in points)

        return (
            f"Dear {name},\n\n"
            f"Thank you for reaching out to our support team.\n\n"
            f"{formatted_points}\n\n"
            f"Please let us know if you have any additional questions or need further assistance.\n\n"
            f"Best regards,\n"
            f"Customer Support Team"
        )


class MockGmailThreadLedger:
    """Tracks sent emails and verifies RFC 2822 / 5322 thread continuity."""

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
        self.escalated_threads: List[Dict[str, Any]] = []
        self.labeled_threads: Dict[str, List[str]] = {}

    def send_reply(
        self,
        thread_id: str,
        in_reply_to_message_id: str,
        to_email: str,
        subject: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Simulates sending a reply that preserves the Gmail conversation thread."""
        sent_id = f"<reply-{len(self.sent_messages) + 1:04d}-{thread_id}@agency.internal>"
        record = {
            "sent_message_id": sent_id,
            "thread_id": thread_id,
            "headers": {
                "In-Reply-To": in_reply_to_message_id,
                "References": in_reply_to_message_id
            },
            "to_email": to_email,
            "subject": subject if subject.startswith("Re:") else f"Re: {subject}",
            "body": body,
            "labels": labels or ["AI-Answered"],
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        self.sent_messages.append(record)
        self.labeled_threads.setdefault(thread_id, []).extend(record["labels"])
        return record

    def escalate_thread(self, thread_id: str, message_id: str, sender_email: str, reason: str, score: float) -> Dict[str, Any]:
        """Simulates adding escalation labels and triggering an internal alert."""
        record = {
            "thread_id": thread_id,
            "message_id": message_id,
            "sender_email": sender_email,
            "reason": reason,
            "score": score,
            "escalated_at": datetime.now(timezone.utc).isoformat()
        }
        self.escalated_threads.append(record)
        self.labeled_threads.setdefault(thread_id, []).append("Needs-Human-Review")
        return record
