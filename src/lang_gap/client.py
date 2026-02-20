"""Async OpenRouter client with rate limiting and retries."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Self

import httpx

from lang_gap.config import (
    MAX_CONCURRENT_PER_MODEL,
    MAX_RETRIES,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    REQUEST_TIMEOUT_S,
)


@dataclass
class CompletionResponse:
    content: str
    latency_ms: int
    tokens_used: int


class OpenRouterClient:
    def __init__(self) -> None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY not set. Copy .env.example to .env and fill it in."
            )
        self._semaphores: dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(MAX_CONCURRENT_PER_MODEL)
        )
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=OPENROUTER_BASE_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "X-Title": "LangBench",
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIMEOUT_S,
            )
        return self._client

    async def complete(self, model_id: str, prompt: str) -> CompletionResponse:
        """Send a single user-message completion request."""
        sem = self._semaphores[model_id]
        async with sem:
            return await self._complete_with_retry(model_id, prompt)

    async def _complete_with_retry(
        self, model_id: str, prompt: str
    ) -> CompletionResponse:
        client = await self._get_client()
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            t0 = time.monotonic()
            try:
                resp = await client.post("/chat/completions", json=payload)
                latency_ms = int((time.monotonic() - t0) * 1000)

                if resp.status_code == 429 or resp.status_code >= 500:
                    last_error = RuntimeError(
                        f"HTTP {resp.status_code}: {resp.text[:200]}"
                    )
                    wait = 2 ** (attempt + 1)
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)

                return CompletionResponse(
                    content=content,
                    latency_ms=latency_ms,
                    tokens_used=tokens,
                )

            except (httpx.HTTPStatusError, httpx.ReadTimeout, KeyError) as exc:
                last_error = exc
                wait = 2 ** (attempt + 1)
                await asyncio.sleep(wait)

        raise RuntimeError(
            f"Failed after {MAX_RETRIES} retries for {model_id}: {last_error}"
        )

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
