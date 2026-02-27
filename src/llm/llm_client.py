"""LLM client abstraction.

Provides a lightweight wrapper around OpenAI's chat-completions API with a
deterministic stub so the bot runs offline (DRY_RUN / CI) with no API key.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass
class LLMMessage:
    role: str   # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    finish_reason: str


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class LLMClientProtocol(Protocol):
    def chat(self, messages: list[LLMMessage], temperature: float = 0.2) -> LLMResponse: ...


# ---------------------------------------------------------------------------
# Stub (no key, deterministic, offline-safe)
# ---------------------------------------------------------------------------


class StubLLMClient:
    """Returns a hard-coded approval response – used when OPENAI_API_KEY is absent."""

    MODEL = "stub"

    def chat(self, messages: list[LLMMessage], temperature: float = 0.2) -> LLMResponse:
        # Return a minimal valid JSON that bet_analyst.py can parse.
        payload = json.dumps({
            "approved": True,
            "confidence": 0.75,
            "reasoning": "Stub LLM: statistical edge is positive; no key provided for real analysis.",
            "stake_multiplier": 1.0,
        })
        return LLMResponse(content=payload, model=self.MODEL, finish_reason="stop")


# ---------------------------------------------------------------------------
# OpenAI client (requires openai>=1.0 and OPENAI_API_KEY)
# ---------------------------------------------------------------------------


class OpenAILLMClient:
    """Thin wrapper around openai.chat.completions. Requires `openai>=1.0`."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 30.0):
        try:
            from openai import OpenAI  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "openai package is required for LLM mode. "
                "Install it with: pip install openai>=1.0"
            ) from exc
        self._client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model

    def chat(self, messages: list[LLMMessage], temperature: float = 0.2) -> LLMResponse:
        raw_messages = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=raw_messages,  # type: ignore[arg-type]
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.warning("OpenAI API call failed: %s – falling back to stub", exc)
            return StubLLMClient().chat(messages, temperature)
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "{}",
            model=response.model,
            finish_reason=choice.finish_reason or "unknown",
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_llm_client(api_key: str = "", model: str = "gpt-4o-mini") -> LLMClientProtocol:
    """Return a real OpenAI client when *api_key* is provided, else the stub."""
    if api_key:
        return OpenAILLMClient(api_key=api_key, model=model)
    return StubLLMClient()
