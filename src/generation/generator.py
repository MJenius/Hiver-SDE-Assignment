"""
src/generation/generator.py
Grounded Response Generator powered by Gemini.
Takes customer message, bounded dialogue context, predicted intent, and top-K retrieved historical cases.
Generates structured JSON draft replies with sentence-level claim attribution to evidence case IDs.
"""

from typing import Dict, Any, List, Optional
import json
from src.llm.gemini_client import GeminiClient
from src.llm.cache import DiskLLMCache

SYSTEM_PROMPT = """You are an expert AppleCare customer support AI assistant.
Your job is to draft a helpful, professional, and concise public reply to a customer tweet.
Follow these strict instructions:
1. Ground your answer strictly in the provided historical support cases and official Apple diagnostic procedures.
2. Do not invent policy, do not fabricate warranty terms, and do not promise unverified refunds or replacement timelines.
3. If the customer needs to perform self-service troubleshooting (e.g., force restart, settings check, cache clearing), state the exact steps clearly.
4. If historical cases suggest asking a diagnostic question (e.g., iOS version, device model), ask it politely.
5. Provide structured JSON output containing the reply text and sentence-level claim attributions to the supporting historical case IDs.
"""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reply": {
            "type": "STRING",
            "description": "The customer-facing reply draft in professional AppleCare voice."
        },
        "claims": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "claim_text": {"type": "STRING"},
                    "evidence_case_ids": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["claim_text", "evidence_case_ids"]
            }
        },
        "suggested_action": {
            "type": "STRING",
            "enum": ["troubleshoot", "ask_clarification", "escalate"]
        }
    },
    "required": ["reply", "claims", "suggested_action"]
}

class GroundedResponseGenerator:
    def __init__(self, client: Optional[GeminiClient] = None):
        if client is None:
            cache = DiskLLMCache()
            self.client = GeminiClient(cache=cache)
        else:
            self.client = client

    def generate_reply(
        self,
        customer_message: str,
        context: str = "",
        intent: str = "unknown",
        retrieved_cases: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        retrieved_cases = retrieved_cases or []
        evidence_blocks = []
        for idx, c in enumerate(retrieved_cases[:3], 1):
            evidence_blocks.append(
                f"[Evidence Case {idx}] (ID: {c.get('case_id')})\n"
                f"Customer Query: {c.get('customer_message')}\n"
                f"Historical Response: {c.get('historical_response')}"
            )
        evidence_str = "\n\n".join(evidence_blocks) if evidence_blocks else "No historical evidence available."

        prompt = f"""Customer Inquiry:
"{customer_message}"

Preceding Conversation Context:
"{context if context else 'None (First turn in thread)'}"

Classified Intent: {intent}

Retrieved Historical Evidence Cases:
{evidence_str}

Please generate the structured response JSON matching the schema."""

        try:
            result = self.client.generate_json(
                prompt=prompt,
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                response_schema=RESPONSE_SCHEMA,
                cache_key_extra={"intent": intent, "context": context}
            )
            return result
        except Exception as e:
            return {
                "reply": "We want to help resolve this. Could you let us know your exact device model and current software version?",
                "claims": [{"claim_text": "Requesting device model and software version", "evidence_case_ids": []}],
                "suggested_action": "ask_clarification",
                "error": str(e)
            }
