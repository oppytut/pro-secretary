from __future__ import annotations

from typing import Any

import httpx

from . import config

_SYSTEM_PERSONA = (
    "Kamu adalah sekretaris pribadi AI yang efisien dan proaktif. "
    "Kamu tahu semua jadwal, task, dan knowledge base user. "
    "Jawab dalam Bahasa Indonesia yang natural, ringkas, dan to-the-point. "
    "Kalau ada context dari knowledge base atau memory, integrasikan ke jawaban."
)


async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    payload: dict[str, Any] = {
        "model": model or config.LLM_MODEL,
        "messages": messages,
        "temperature": temperature if temperature is not None else config.LLM_TEMPERATURE,
        "max_tokens": max_tokens or config.LLM_MAX_TOKENS,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{config.LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
            json=payload,
        )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


async def chat_with_persona(
    user_message: str,
    context_snippets: list[str] | None = None,
    model: str | None = None,
) -> str:
    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PERSONA}]
    if context_snippets:
        ctx = "\n\n".join(f"- {s}" for s in context_snippets)
        messages.append(
            {
                "role": "system",
                "content": f"Context relevan dari memory/knowledge:\n{ctx}",
            }
        )
    messages.append({"role": "user", "content": user_message})
    return await chat_completion(messages, model=model)
