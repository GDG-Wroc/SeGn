import json
import re
from typing import Any

import httpx

from app.core.config import config


class LLMClient:
    def __init__(self) -> None:
        self.base_url = (config.ANALOGY_LLM_BASE_URL or "").rstrip("/")
        self.api_key = config.ANALOGY_LLM_API_KEY
        self.model = config.ANALOGY_LLM_MODEL
        self.timeout = config.ANALOGY_LLM_TIMEOUT
        self.enabled = config.ANALOGY_LLM_ENABLED and bool(self.base_url)

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return parse_json_object(content)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        parsed = json.loads(fenced.group(1))
        if isinstance(parsed, dict):
            return parsed

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("LLM response did not contain a JSON object")
