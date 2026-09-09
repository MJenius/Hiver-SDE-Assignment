"""
src/llm/gemini_client.py
Zero-dependency Gemini REST client supporting Gemini models with:
- Configurable GEMINI_API_KEY and GEMINI_MODEL via environment or direct pass
- Strict exponential backoff retry logic for rate limits (429) and transient errors (500, 503)
- Strict JSON schema structured output parsing
- Pluggable disk caching to avoid redundant API expenditures
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

DEFAULT_MODEL = "gemini-2.5-flash-lite"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

class GeminiAPIError(Exception):
    pass

class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        cache: Optional[Any] = None,
        max_retries: int = 4,
        timeout: int = 30
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
        self.cache = cache
        self.max_retries = max_retries
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 800,
        response_schema: Optional[Dict[str, Any]] = None,
        cache_key_extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Executes generation against Gemini API with caching and exponential backoff retries.
        """
        # 1. Check cache if configured
        if self.cache:
            cache_payload = {
                "model": self.model,
                "prompt": prompt,
                "system_instruction": system_instruction,
                "temperature": temperature,
                "response_schema": response_schema,
                "extra": cache_key_extra or {}
            }
            cached_resp = self.cache.get(cache_payload)
            if cached_resp is not None:
                return cached_resp

        # 2. Build REST request body
        url = f"{API_BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        
        contents = [{"parts": [{"text": prompt}]}]
        req_body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens
            }
        }
        
        if system_instruction:
            req_body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if response_schema:
            req_body["generationConfig"]["responseMimeType"] = "application/json"
            req_body["generationConfig"]["responseSchema"] = response_schema

        headers = {"Content-Type": "application/json"}
        req_bytes = json.dumps(req_body).encode("utf-8")

        # 3. Execute with exponential backoff
        delay = 2.0
        last_error = None

        for attempt in range(self.max_retries):
            try:
                request = urllib.request.Request(url, data=req_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw_data = response.read().decode("utf-8")
                    parsed = json.loads(raw_data)
                    candidates = parsed.get("candidates", [])
                    if not candidates:
                        raise GeminiAPIError("No candidates returned from Gemini API")
                    text_out = candidates[0]["content"]["parts"][0]["text"]
                    
                    # Store in cache
                    if self.cache:
                        self.cache.set(cache_payload, text_out)
                        
                    return text_out
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8", errors="replace")
                last_error = f"HTTP {e.code}: {err_text}"
                if e.code in (429, 500, 503, 504):
                    time.sleep(delay)
                    delay *= 2.0
                else:
                    raise GeminiAPIError(f"Fatal Gemini HTTP Error: {last_error}")
            except Exception as e:
                last_error = str(e)
                time.sleep(delay)
                delay *= 2.0

        raise GeminiAPIError(f"Gemini API request failed after {self.max_retries} retries: {last_error}")

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        response_schema: Optional[Dict[str, Any]] = None,
        cache_key_extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes generate and parses response string into validated JSON dictionary.
        """
        resp_str = self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            response_schema=response_schema,
            cache_key_extra=cache_key_extra
        )
        # Strip potential markdown fences if present
        clean_str = resp_str.strip()
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        elif clean_str.startswith("```"):
            clean_str = clean_str[3:]
        if clean_str.endswith("```"):
            clean_str = clean_str[:-3]
        clean_str = clean_str.strip()

        try:
            return json.loads(clean_str)
        except Exception as e:
            raise GeminiAPIError(f"Failed to parse model output as JSON: {e}\nRaw content:\n{resp_str}")
