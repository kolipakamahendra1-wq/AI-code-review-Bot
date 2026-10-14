"""Provider-pluggable LLM layer. Every client takes (system, user) and returns raw text."""
import json
from typing import Protocol

import httpx

from . import config


class LLMClient(Protocol):
    name: str

    def complete(self, system: str, user: str) -> str: ...


class LLMError(RuntimeError):
    pass


def _post(url: str, **kw) -> dict:
    try:
        r = httpx.post(url, timeout=config.LLM_TIMEOUT, **kw)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise LLMError(f"LLM request failed ({e.response.status_code}): {e.response.text[:300]}") from e
    except httpx.HTTPError as e:
        raise LLMError(f"LLM request failed: {e}") from e


class OllamaClient:
    def __init__(self, url: str | None = None, model: str | None = None):
        self.url = (url or config.OLLAMA_URL).rstrip("/")
        self.model = model or config.CHAT_MODEL
        self.name = f"ollama:{self.model}"

    def complete(self, system: str, user: str) -> str:
        data = _post(
            f"{self.url}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "format": "json",
                # repeat_penalty/num_predict stop small models looping inside JSON mode
                "options": {"temperature": 0.2, "num_ctx": 8192, "repeat_penalty": 1.15,
                            "num_predict": 1200},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        return data["message"]["content"]


class OpenAIClient:
    def __init__(self, key: str | None = None, model: str | None = None):
        self.key = key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        self.name = f"openai:{self.model}"

    def complete(self, system: str, user: str) -> str:
        data = _post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={
                "model": self.model,
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        return data["choices"][0]["message"]["content"]


class AnthropicClient:
    def __init__(self, key: str | None = None, model: str | None = None):
        self.key = key or config.ANTHROPIC_API_KEY
        self.model = model or config.ANTHROPIC_MODEL
        self.name = f"anthropic:{self.model}"

    def complete(self, system: str, user: str) -> str:
        data = _post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self.key, "anthropic-version": "2023-06-01"},
            json={
                "model": self.model,
                "max_tokens": 2048,
                "temperature": 0.1,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        return "".join(b.get("text", "") for b in data["content"])


class RulesOnlyClient:
    """No model call: the deterministic rule engine does all the work (instant, offline)."""

    name = "rules-only"

    def complete(self, system: str, user: str) -> str:
        return '{"summary": "", "findings": []}'


class FakeClient:
    """Deterministic client for tests."""

    def __init__(self, responses):
        self.name = "fake"
        self.responses = [responses] if isinstance(responses, (str, dict)) else list(responses)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        r = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        return r if isinstance(r, str) else json.dumps(r)


def get_client() -> LLMClient:
    p = config.LLM_PROVIDER.lower()
    if p == "rules":  # no model at all: deterministic rule engine only
        return RulesOnlyClient()
    if p == "openai":
        if not config.OPENAI_API_KEY:
            raise LLMError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set")
        return OpenAIClient()
    if p == "anthropic":
        if not config.ANTHROPIC_API_KEY:
            raise LLMError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set")
        return AnthropicClient()
    return OllamaClient()
