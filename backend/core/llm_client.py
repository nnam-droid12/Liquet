"""
Centralized LLM client for Liquet.

Design:
- Wraps the OpenAI-compatible Qwen endpoint with tenacity retries and timeouts.
- Two named model slots: REASONING (qwen-plus / qwen3.7-max) and VISION (qwen-vl-plus / qwen3.6-plus).
- Structured output via response_format={"type": "json_object"} + Pydantic parsing.
- Never trusts raw text — always parses into a typed schema.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional, Type, TypeVar

import httpx
from openai import AsyncOpenAI, APIConnectionError, APIStatusError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Retryable errors
_RETRYABLE = (APIConnectionError, RateLimitError, httpx.TransportError)


def _make_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.qwen_api_key,
        base_url=settings.qwen_base_url,
        timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=5.0),
        max_retries=0,  # we handle retries via tenacity
    )


_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = _make_client()
    return _client


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def chat_completion(
    messages: list[dict[str, Any]],
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    json_mode: bool = False,
) -> str:
    """Raw chat completion; returns the assistant message string."""
    model = model or settings.active_reasoning_model
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    client = get_client()
    response = await client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    logger.debug("LLM [%s] tokens=%s", model, response.usage)
    return content


async def structured_chat(
    messages: list[dict[str, Any]],
    schema: Type[T],
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> T:
    """Chat completion that parses the response into a Pydantic model via JSON mode."""
    system_schema_hint = (
        f"\nRespond ONLY with valid JSON matching this schema:\n"
        f"{json.dumps(schema.model_json_schema(), indent=2)}"
    )
    # Inject schema hint into last system message or prepend
    augmented = list(messages)
    if augmented and augmented[0]["role"] == "system":
        augmented[0] = {
            **augmented[0],
            "content": augmented[0]["content"] + system_schema_hint,
        }
    else:
        augmented.insert(0, {"role": "system", "content": system_schema_hint.strip()})

    raw = await chat_completion(
        augmented, model=model, temperature=temperature,
        max_tokens=max_tokens, json_mode=True,
    )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("LLM returned non-JSON: %s", raw[:500])
        raise ValueError(f"LLM did not return valid JSON: {exc}") from exc

    return schema.model_validate(data)


async def vision_completion(
    text_prompt: str,
    image_url: str,
    model: Optional[str] = None,
) -> str:
    """Single-image vision completion using the vision model."""
    model = model or settings.model_vision
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
                {"type": "text", "text": text_prompt},
            ],
        }
    ]
    return await chat_completion(messages, model=model, temperature=0.0, max_tokens=2048)


async def smoke_test() -> dict[str, str]:
    """Verifies connectivity to QwenCloud. Used in startup and CI."""
    content = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Reply with exactly: LIQUET_OK",
            },
            {"role": "user", "content": "Ping."},
        ],
        max_tokens=16,
    )
    return {"status": "ok", "response": content.strip()}
