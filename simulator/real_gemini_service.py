"""
Real Gemini API Service connecting to Google AI Studio.
Uses actual live API calls for:
1. Intent Classification (gemini-3.1-flash-lite / JSON schema)
2. Vector Embeddings (gemini-embedding-001)
3. Grounded Customer Response Generation (gemini-3.1-flash-lite)
"""

import urllib.request
import json
import math
from typing import Dict, Any, List, Optional

import os
from pathlib import Path

# Load GEMINI_API_KEY from environment or local .env
def _load_api_key() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("GEMINI_API_KEY=", 1)[1].strip()
    return ""

GEMINI_API_KEY = _load_api_key()
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculates cosine similarity between two vector lists."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class RealGeminiService:
    """Connects to live Google AI Studio Gemini API."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = "gemini-3.1-flash-lite"):
        self.api_key = api_key
        self.model_name = model_name
        self.embed_model = "gemini-embedding-001"

    def _call_gemini(self, endpoint: str, payload: Dict[str, Any], timeout: int = 60, max_retries: int = 2) -> Dict[str, Any]:
        url = f"{BASE_URL}/{endpoint}?key={self.api_key}"
        data = json.dumps(payload).encode("utf-8")

        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as err:
                if attempt < max_retries:
                    import time
                    time.sleep(2)
                    continue
                raise err

    def get_embedding(self, text: str) -> List[float]:
        """Calls Google AI Studio to compute real vector embeddings."""
        payload = {
            "content": {
                "parts": [{"text": text}]
            }
        }
        res = self._call_gemini(f"models/{self.embed_model}:embedContent", payload)
        return res["embedding"]["values"]

    def classify_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Calls live Gemini to classify email into support vs non-support, category, and core query."""
        prompt = (
            "You are an AI customer support triage agent. Analyze the email subject and body.\n"
            "Return a strictly valid JSON object with the following fields:\n"
            "- \"is_support_request\": boolean (true if technical, refund, billing, account, product inquiry; false if spam, cold marketing pitch, newsletter, recruitment)\n"
            "- \"category\": string (one of: 'technical_issue', 'billing_refund', 'account_access', 'feature_question', 'general_inquiry', 'non_support')\n"
            "- \"urgency\": string (one of: 'low', 'medium', 'high')\n"
            "- \"core_query\": string (distilled 1-sentence search query summarizing the customer's core question for vector search)\n\n"
            f"Subject: {subject}\n"
            f"Body: {body}\n"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        res = self._call_gemini(f"models/{self.model_name}:generateContent", payload)
        text_content = res["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text_content)

    def generate_response(self, customer_name: str, inquiry: str, context_docs: List[Dict[str, Any]]) -> str:
        """Calls live Gemini to generate context-grounded customer support reply."""
        context_str = "\n---\n".join(f"Title: {d['title']}\nContent: {d['text']}" for d in context_docs)

        prompt = (
            "You are a professional, courteous customer support representative for our agency.\n"
            "Answer the customer's question STRICTLY based on the provided Knowledge Base Context below.\n"
            "Rules:\n"
            "1. If a detail is not in the context, do not invent or promise it.\n"
            "2. Keep the greeting professional and reference their query.\n"
            "3. Format cleanly with bullet points where appropriate.\n"
            "4. Sign off as 'Customer Support Team'.\n\n"
            f"Customer Name: {customer_name}\n"
            f"Customer Inquiry: {inquiry}\n\n"
            f"Knowledge Base Context:\n{context_str}\n"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2
            }
        }

        res = self._call_gemini(f"models/{self.model_name}:generateContent", payload)
        return res["candidates"][0]["content"]["parts"][0]["text"].strip()
