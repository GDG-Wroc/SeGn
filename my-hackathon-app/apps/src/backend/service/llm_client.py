import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


class LLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        self.base_url = (base_url or os.getenv("LOCAL_LLM_BASE_URL") or "http://localhost:1234/v1").rstrip("/")
        self.model = model or os.getenv("LOCAL_LLM_MODEL") or "local-model"
        self.timeout = timeout

    async def explain_mcp_response(self, user_query: str, mcp_response: Any) -> dict[str, Any]:
        prompt = self._build_prompt(user_query, mcp_response)

        try:
            llm_answer = await self._send_chat_completion(prompt)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            return {
                "answer": (
                    "Nie udalo mi sie polaczyc z lokalnym modelem LLM. "
                    "Ponizej zwracam surowa odpowiedz z MCP."
                ),
                "raw_mcp_response": mcp_response,
                "llm_error": str(exc),
            }

        return {
            "answer": llm_answer,
            "raw_mcp_response": mcp_response,
        }

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "Jestes pomocnym asystentem naukowym R&D.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload)

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    async def _send_chat_completion(self, prompt: str) -> str:
        system_prompt = (
            "Jestes asystentem, ktory zamienia techniczne odpowiedzi MCP "
            "na krotkie, zrozumiale komunikaty po polsku. "
            "Nie wymyslaj faktow spoza danych. Jesli danych brakuje, powiedz to jasno."
        )
        return await self.generate_text(prompt, system_prompt)

    def _build_prompt(self, user_query: str, mcp_response: Any) -> str:
        return (
            "Pytanie uzytkownika:\n"
            f"{user_query}\n\n"
            "Surowa odpowiedz z MCP:\n"
            f"{self._to_json(mcp_response)}\n\n"
            "Napisz dla uzytkownika jasna odpowiedz. "
            "Podsumuj najwazniejsze wyniki i unikaj technicznego JSON-a."
        )

    def _to_json(self, value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, indent=2, default=str)
        except TypeError:
            return str(value)
