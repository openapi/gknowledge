"""OpenAI-compatible HTTP provider.

Works with the OpenAI API and any endpoint that speaks the same
``/chat/completions`` contract (Ollama, LM Studio, vLLM, OpenRouter, Together,
Groq, ...). Uses only the standard library so the app has no hard runtime
dependency on a vendor SDK.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .base import LLMMessage, LLMProvider, LLMResponse, ProviderError

_TIMEOUT = 900  # long ingests should not fail prematurely (README requirement)


class OpenAICompatibleProvider(LLMProvider):
    kind = "llm"

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        embed_model: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.embed_model = embed_model
        self.name = f"OpenAI-compatible ({model})"

    def available(self) -> bool:
        # Local endpoints (Ollama etc.) legitimately need no key.
        return bool(self.base_url)

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            body = exc.read().decode("utf-8", "replace")
            raise ProviderError(f"HTTP {exc.code}: {body[:400]}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network
            raise ProviderError(f"Connection failed: {exc.reason}") from exc

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        json_object: bool = False,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        payload: dict = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if json_object:
            payload["response_format"] = {"type": "json_object"}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        data = self._post("/chat/completions", payload)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"Unexpected response shape: {data}") from exc
        usage = data.get("usage", {})
        return LLMResponse(
            content=content or "",
            model=data.get("model", self.model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            raw=data,
        )



DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OLLAMA_MODELS_URL = f"{DEFAULT_OLLAMA_BASE_URL}/models"
_OLLAMA_TIMEOUT = 2.0


class OllamaUnavailable(ProviderError):
    """Nothing answered at the Ollama endpoint (refused, unreachable or timed out)."""


def discover_ollama_models(
    endpoint: str = DEFAULT_OLLAMA_MODELS_URL,
    *,
    timeout: float = _OLLAMA_TIMEOUT,
) -> list[str]:
    """Return the model IDs a local Ollama server offers.

    One GET to the OpenAI-compatible ``/v1/models`` endpoint with a short
    timeout and no request body, so no document content can leave the app.

    Raises:
        OllamaUnavailable: nothing is listening, or it did not answer in time.
        ProviderError: the server answered with an HTTP error or an
            unexpected payload.
    """
    req = urllib.request.Request(endpoint, method="GET")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise ProviderError(f"HTTP {exc.code}: {body[:200]}") from exc
    except urllib.error.URLError as exc:
        raise OllamaUnavailable(f"Connection failed: {exc.reason}") from exc
    except OSError as exc:  # TimeoutError, ConnectionResetError, ...
        raise OllamaUnavailable(f"Connection failed: {exc}") from exc

    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise ProviderError(f"Invalid JSON response: {exc}") from exc

    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise ProviderError(f"Unexpected response shape: {raw[:200]}")
    models: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ProviderError(f"Unexpected model entry: {str(item)[:200]}")
        models.append(item["id"])
    return models


def should_prefill_ollama_base_url(current_base_url: str | None) -> bool:
    """True when the Base URL is empty or still the OpenAI default.

    Anything else was entered by the user and must not be overwritten.
    """
    cleaned = (current_base_url or "").strip().rstrip("/")
    return not cleaned or cleaned == "https://api.openai.com/v1"


def resolve_ollama_model_selection(
    current_model: str,
    discovered_models: list[str],
) -> tuple[int, str, bool]:
    """Pick the dropdown entry for ``current_model`` among ``discovered_models``.

    The dropdown lists the discovered models followed by a "Custom…" entry at
    index ``len(discovered_models)``. Returns ``(index, model, is_custom)``:
    a known model selects itself, an unknown one selects "Custom…" and keeps
    its name, and no model at all selects the first discovered one.
    """
    if not discovered_models:
        return 0, current_model, True
    if current_model in discovered_models:
        return discovered_models.index(current_model), current_model, False
    if current_model:
        return len(discovered_models), current_model, True
    return 0, discovered_models[0], False


def get_ollama_selection_state(
    selected_idx: int,
    models: list[str],
) -> tuple[str | None, bool]:
    """Map a dropdown index to ``(model, is_custom)``.

    ``models`` excludes the trailing "Custom…" entry. A discovered model gives
    ``(name, False)``, the "Custom…" entry ``(None, True)``, and anything else
    (including GTK's invalid position) ``(None, False)``.
    """
    if 0 <= selected_idx < len(models):
        return models[selected_idx], False
    if selected_idx == len(models):
        return None, True
    return None, False
