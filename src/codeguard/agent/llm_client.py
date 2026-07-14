from __future__ import annotations
from abc import ABC, abstractmethod
from codeguard.models.entities import Message, LLMResponse


class LLMClient(ABC):
    @abstractmethod
    async def call(self, messages: list[Message]) -> LLMResponse:
        ...


class MockLLMClient(LLMClient):
    def __init__(self, responses: list[LLMResponse]):
        self._responses = responses
        self._index = 0

    async def call(self, messages: list[Message]) -> LLMResponse:
        response = self._responses[self._index]
        self._index += 1
        return response


class RealLLMClient(LLMClient):
    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4"):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model

    async def call(self, messages: list[Message]) -> LLMResponse:
        import httpx

        url = self._base_url
        if not url.endswith("/v1/chat/completions"):
            if url.endswith("/v1"):
                url = f"{url}/chat/completions"
            else:
                url = f"{url}/v1/chat/completions"

        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                tool_calls=[],
            )
