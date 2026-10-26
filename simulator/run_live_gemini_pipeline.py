"""
Live Pipeline Execution against Google AI Studio Gemini API.
Runs realistic customer email scenarios through live LLM classification,
live 3072-dim vector embedding, and live grounded response generation.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.real_gemini_service import RealGeminiService
from simulator.real_vector_store import RealGeminiVectorStore
from simulator.fixtures import TEST_SCENARIOS, KNOWLEDGE_BASE_ARTICLES
from simulator.mock_services import MockGmailThreadLedger


def run_live_pipeline():
    print("=" * 80)
    print("AI CUSTOMER SUPPORT EMAIL WORKFLOW - LIVE GOOGLE GEMINI EXECUTION")
    print("Mode: REAL API CALLS (gemini-3.1-flash-lite & gemini-embedding-001)")
    print("=" * 80)

    gemini = RealGeminiService()
    vector_store = RealGeminiVectorStore(gemini, KNOWLEDGE_BASE_ARTICLES)
    vector_store.build_index()

    gmail_ledger = MockGmailThreadLedger()
    confidence_threshold = 0.60  # Standard threshold for 3072-dim Gemini cosine vectors

    # Run select representative scenarios
    selected_scenarios = [
        TEST_SCENARIOS[0],  # TC_01: Refund inquiry (Should match & generate real reply)
        TEST_SCENARIOS[1],  # TC_02: Cold spam outreach (Should be classified non-support & dropped)
        TEST_SCENARIOS[2],  # TC_03: Obscure query (Should fall below threshold & escalate to human)
        TEST_SCENARIOS[3],  # TC_04: Thread continuity follow-up
    ]

    for tc in selected_scenarios:
        s_id = tc["scenario_id"]
        s_name = tc["name"]
        email = tc["input_email"]

        print(f"\n" + "-" * 75)
        print(f"[{s_id}] {s_name}")
        print(f"  From: {email['sender_name']} <{email['sender_email']}>")
        print(f"  Subject: '{email['subject']}'")
        print(f"  Body: '{email['body'][:80]}...'")

        # 1. Live Gemini Intent Classification
        print("  --> Calling Live Gemini API for Intent Classification...")
        classification = gemini.classify_email(email["subject"], email["body"])
        print(f"  [Classification Result] is_support: {classification.get('is_support_request')}, "
              f"category: {classification.get('category')}, urgency: {classification.get('urgency')}")
        print(f"  [Core Query]: '{classification.get('core_query')}'")

        if not classification.get("is_support_request", False):
            print("  [Action] --> NON-SUPPORT EMAIL DETECTED. Pipeline exits cleanly without sending reply.")
            continue

        # 2. Live Gemini Vector Embedding & Search
        core_query = classification.get("core_query") or email["subject"]
        print(f"  --> Calling Live Gemini API for Query Embedding & Vector Search...")
        rag_res = vector_store.query(core_query, top_k=3)
        highest_score = rag_res["highest_score"]
        best_doc = rag_res["matches"][0] if rag_res["matches"] else None

        print(f"  [Vector Search Result] Top match: '{best_doc['title']}' | Cosine Score: {highest_score}")

        # 3. Confidence Threshold Guardrail
        if highest_score < confidence_threshold:
            print(f"  [Escalation Gate] Similarity score {highest_score} is BELOW threshold ({confidence_threshold})!")
            print(f"  --> Action: Tagged Gmail thread with 'Needs-Human-Review'. Escalation alert sent to agency team.")
            gmail_ledger.escalate_thread(
                thread_id=email["thread_id"],
                message_id=email["message_id"],
                sender_email=email["sender_email"],
                reason=f"Confidence score {highest_score} below threshold {confidence_threshold}",
                score=highest_score
            )
            continue

        # 4. Live Gemini Response Generation
        print(f"  [Resolution Gate] Similarity score {highest_score} >= {confidence_threshold} (High Confidence).")
        print(f"  --> Calling Live Gemini API to generate grounded response...")
        ai_reply = gemini.generate_response(
            customer_name=email.get("sender_name", ""),
            inquiry=email["body"],
            context_docs=[best_doc]
        )

        print("\n  [LIVE GEMINI GENERATED RESPONSE]:")
        for line in ai_reply.splitlines():
            print(f"    {line}")

        # 5. Record Gmail Reply with Thread Continuity
        reply_record = gmail_ledger.send_reply(
            thread_id=email["thread_id"],
            in_reply_to_message_id=email["message_id"],
            to_email=email["sender_email"],
            subject=email["subject"],
            body=ai_reply
        )
        print(f"\n  [Delivered on Thread] threadId: {reply_record['thread_id']} | In-Reply-To: {reply_record['headers']['In-Reply-To']}")

    print("\n" + "=" * 80)
    print("LIVE PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"Total Sent Replies: {len(gmail_ledger.sent_messages)} | Total Escalated: {len(gmail_ledger.escalated_threads)}")
    print("=" * 80)


if __name__ == "__main__":
    run_live_pipeline()
