"""
eval/judge/llm_judge.py
Independent LLM-as-Judge using Gemini.
Implements:
- 1 to 5 Rubric Scoring (Groundedness, Actionability, Relevance, Brand Consistency)
- Pairwise Comparative Judgment with Position Bias Swapping ((A, B) and (B, A))
- Strict JSON output parsing
"""

from typing import Dict, Any, List, Optional
from src.llm.gemini_client import GeminiClient
from src.llm.cache import DiskLLMCache

JUDGE_SYSTEM_PROMPT = """You are an impartial, highly rigorous expert judge evaluating customer support replies for AppleCare.
Score customer support responses objectively on a 1-5 integer scale across these axes:
1. Groundedness (1-5): 5 = completely grounded in evidence; 1 = completely fabricated/hallucinated policy or facts.
2. Actionability (1-5): 5 = concrete, clear executable steps; 1 = vague brush-off or unhelpful deflection.
3. Relevance (1-5): 5 = directly solves the specific symptom asked; 1 = addresses wrong problem.
4. Brand Consistency (1-5): 5 = empathetic, professional, concise AppleCare voice; 1 = unprofessional, abrasive, or overly verbose.
Output strict JSON."""

PAIRWISE_SYSTEM_PROMPT = """You are an impartial expert judge evaluating two customer support replies for AppleCare.
Given a customer inquiry and the available historical evidence, determine which response is better.
You must choose one of:
- "A" (Response A is noticeably better)
- "B" (Response B is noticeably better)
- "tie" (Both responses are equally good or equally flawed)
Output strict JSON."""

SCORE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "groundedness": {"type": "INTEGER"},
        "actionability": {"type": "INTEGER"},
        "relevance": {"type": "INTEGER"},
        "brand_consistency": {"type": "INTEGER"},
        "overall_score": {"type": "NUMBER"},
        "critique": {"type": "STRING"}
    },
    "required": ["groundedness", "actionability", "relevance", "brand_consistency", "overall_score", "critique"]
}

PAIRWISE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "preferred": {"type": "STRING", "enum": ["A", "B", "tie"]},
        "reason": {"type": "STRING"}
    },
    "required": ["preferred", "reason"]
}

class LLMJudge:
    def __init__(self, client: Optional[GeminiClient] = None):
        if client is None:
            cache = DiskLLMCache()
            self.client = GeminiClient(cache=cache)
        else:
            self.client = client

    def score_single(
        self,
        customer_message: str,
        response_text: str,
        evidence_text: str = ""
    ) -> Dict[str, Any]:
        prompt = f"""Customer Inquiry:
"{customer_message}"

Support Response to Evaluate:
"{response_text}"

Available Reference Evidence:
"{evidence_text if evidence_text else 'None provided'}"

Provide 1-5 ratings across the 4 axes."""
        try:
            return self.client.generate_json(
                prompt=prompt,
                system_instruction=JUDGE_SYSTEM_PROMPT,
                temperature=0.0,
                response_schema=SCORE_SCHEMA,
                cache_key_extra={"eval_target": response_text}
            )
        except Exception as e:
            return {
                "groundedness": 3,
                "actionability": 3,
                "relevance": 3,
                "brand_consistency": 3,
                "overall_score": 3.0,
                "critique": f"Judge error: {e}"
            }

    def compare_pairwise(
        self,
        customer_message: str,
        response_a: str,
        response_b: str,
        evidence_text: str = ""
    ) -> Dict[str, Any]:
        """
        Runs position-swapped comparison to detect and mitigate position bias.
        """
        # Pass 1: (A, B)
        p1 = f"""Customer Inquiry:
"{customer_message}"

Reference Evidence:
"{evidence_text}"

Response A:
"{response_a}"

Response B:
"{response_b}"

Which response is better?"""

        # Pass 2: (B, A) [swapped]
        p2 = f"""Customer Inquiry:
"{customer_message}"

Reference Evidence:
"{evidence_text}"

Response A:
"{response_b}"

Response B:
"{response_a}"

Which response is better?"""

        try:
            r1 = self.client.generate_json(prompt=p1, system_instruction=PAIRWISE_SYSTEM_PROMPT, temperature=0.0, response_schema=PAIRWISE_SCHEMA)
            r2 = self.client.generate_json(prompt=p2, system_instruction=PAIRWISE_SYSTEM_PROMPT, temperature=0.0, response_schema=PAIRWISE_SCHEMA)

            choice_1 = r1.get("preferred", "tie")
            # In pass 2, "A" actually means response B, and "B" means response A
            raw_choice_2 = r2.get("preferred", "tie")
            choice_2 = "B" if raw_choice_2 == "A" else ("A" if raw_choice_2 == "B" else "tie")

            is_consistent = (choice_1 == choice_2)
            final_winner = choice_1 if is_consistent else "tie"

            return {
                "winner": final_winner,
                "pass_1_choice": choice_1,
                "pass_2_choice": choice_2,
                "is_consistent": is_consistent,
                "reason": r1.get("reason", "")
            }
        except Exception as e:
            return {
                "winner": "tie",
                "pass_1_choice": "tie",
                "pass_2_choice": "tie",
                "is_consistent": True,
                "reason": f"Judge error: {e}"
            }
