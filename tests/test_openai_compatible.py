"""Ollama model discovery against a fake local server (no network, no Ollama)."""

from __future__ import annotations

import http.server
import json
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gknowledge.providers.base import ProviderError
from gknowledge.providers.openai_compatible import (
    DEFAULT_OLLAMA_MODELS_URL,
    OllamaUnavailable,
    discover_ollama_models,
    get_ollama_selection_state,
    resolve_ollama_model_selection,
    should_prefill_ollama_base_url,
)


class FakeOllama:
    """Serves one canned answer on /v1/models and records every request."""

    def __init__(self, body: str | bytes = "", status: int = 200, delay: float = 0.0):
        self.requests: list[tuple[str, str, int]] = []
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def _record(self):
                length = int(self.headers.get("Content-Length") or 0)
                outer.requests.append((self.command, self.path, length))

            def do_GET(self):  # noqa: N802
                self._record()
                time.sleep(delay)
                data = body.encode() if isinstance(body, str) else body
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except OSError:  # client already gave up (timeout test)
                    pass

            def do_POST(self):  # noqa: N802
                self._record()
                self.send_response(405)
                self.end_headers()

            def log_message(self, *_a):
                pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1/models"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def ollama():
    servers: list[FakeOllama] = []

    def start(*a, **kw) -> FakeOllama:
        servers.append(FakeOllama(*a, **kw))
        return servers[-1]

    yield start
    for s in servers:
        s.close()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_default_endpoint_is_local_ollama():
    assert DEFAULT_OLLAMA_MODELS_URL == "http://localhost:11434/v1/models"


def test_discovers_model_ids_with_a_single_bodyless_get(ollama):
    server = ollama(json.dumps({"object": "list", "data": [
        {"id": "llama3.2:latest", "object": "model", "owned_by": "library"},
        {"id": "qwen2.5:7b", "object": "model"},
    ]}))
    assert discover_ollama_models(server.url) == ["llama3.2:latest", "qwen2.5:7b"]
    assert server.requests == [("GET", "/v1/models", 0)]


def test_server_without_models_returns_empty_list(ollama):
    server = ollama(json.dumps({"object": "list", "data": []}))
    assert discover_ollama_models(server.url) == []


def test_refused_connection_means_no_server():
    url = f"http://127.0.0.1:{_free_port()}/v1/models"
    with pytest.raises(OllamaUnavailable):
        discover_ollama_models(url)


def test_slow_server_times_out_as_unavailable(ollama):
    server = ollama('{"data": []}', delay=1.0)
    start = time.monotonic()
    with pytest.raises(OllamaUnavailable):
        discover_ollama_models(server.url, timeout=0.2)
    assert time.monotonic() - start < 1.0


def test_default_timeout_is_short():
    assert discover_ollama_models.__kwdefaults__["timeout"] <= 2.0


@pytest.mark.parametrize("body, message", [
    ("<html>502 Bad Gateway</html>", "Invalid JSON"),
    (json.dumps(["not", "a", "dict"]), "Unexpected response shape"),
    (json.dumps({"error": "unsupported"}), "Unexpected response shape"),
    (json.dumps({"data": "llama3.2"}), "Unexpected response shape"),
    (json.dumps({"data": [{"name": "llama3.2"}]}), "Unexpected model entry"),
])
def test_malformed_answers_raise_a_clear_error(ollama, body, message):
    server = ollama(body)
    with pytest.raises(ProviderError) as exc:
        discover_ollama_models(server.url)
    assert message in str(exc.value)
    assert not isinstance(exc.value, OllamaUnavailable)


def test_http_error_is_reported_with_status(ollama):
    server = ollama('{"error": "boom"}', status=500)
    with pytest.raises(ProviderError, match="HTTP 500"):
        discover_ollama_models(server.url)


def test_base_url_prefilled_only_when_empty_or_openai_default():
    assert should_prefill_ollama_base_url("")
    assert should_prefill_ollama_base_url("   ")
    assert should_prefill_ollama_base_url(None)
    assert should_prefill_ollama_base_url("https://api.openai.com/v1/")
    assert not should_prefill_ollama_base_url("http://localhost:11434/v1")
    assert not should_prefill_ollama_base_url("http://192.168.1.50:11434/v1")
    assert not should_prefill_ollama_base_url("https://proxy.internal/v1")


def test_saved_model_is_preselected_when_discovered():
    models = ["llama3.2:latest", "mistral:latest"]
    assert resolve_ollama_model_selection("mistral:latest", models) == (1, "mistral:latest", False)


def test_unknown_saved_model_selects_custom_and_keeps_its_name():
    models = ["llama3.2:latest", "mistral:latest"]
    assert resolve_ollama_model_selection("my-lora", models) == (2, "my-lora", True)


def test_no_saved_model_selects_first_discovered():
    assert resolve_ollama_model_selection("", ["llama3.2:latest"]) == (0, "llama3.2:latest", False)


def test_nothing_discovered_keeps_free_text_model():
    assert resolve_ollama_model_selection("my-model", []) == (0, "my-model", True)


def test_dropdown_index_maps_to_model_or_custom():
    models = ["llama3.2:latest", "qwen2.5:7b"]
    assert get_ollama_selection_state(1, models) == ("qwen2.5:7b", False)
    assert get_ollama_selection_state(2, models) == (None, True)  # "Custom…"
    assert get_ollama_selection_state(-1, models) == (None, False)
    assert get_ollama_selection_state(0xFFFFFFFF, models) == (None, False)  # GTK_INVALID_LIST_POSITION
