"""ローカルLLMクライアント (Ollama / LM Studio などの OpenAI 互換サーバー)。標準ライブラリのみ使用。"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

BACKENDS = ("ollama", "lmstudio")
DEFAULT_BACKEND = os.environ.get("VIDPROMPT_BACKEND") or "lmstudio"
DEFAULT_HOSTS = {
    "ollama": os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    "lmstudio": os.environ.get("LMSTUDIO_HOST", "http://localhost:1234"),
}
DEFAULT_MODELS = {"ollama": "qwen2.5:7b", "lmstudio": None}  # LM Studio は読み込み中のモデルを自動使用


class LLMError(RuntimeError):
    pass


class _HTTPClient:
    name = "LLM"
    hint = ""

    def __init__(self, host: str, model: str | None, timeout: float = 300):
        if not host.startswith("http"):
            host = "http://" + host
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        req = urllib.request.Request(
            self.host + path,
            data=None if payload is None else json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise LLMError(f"{self.name} がエラーを返しました ({e.code}): {body}") from e
        except urllib.error.URLError as e:
            raise LLMError(f"{self.name} に接続できません ({self.host})。{self.hint}: {e.reason}") from e


class OllamaClient(_HTTPClient):
    name = "Ollama"
    hint = "`ollama serve` が起動しているか確認してください"

    def chat(self, system: str, user: str, *, json_schema: dict[str, Any] | None = None,
             temperature: float = 0.4) -> str:
        payload: dict[str, Any] = {
            "model": self.model or DEFAULT_MODELS["ollama"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_schema is not None:
            payload["format"] = json_schema
        data = self._request("/api/chat", payload)
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as e:
            raise LLMError(f"想定外のレスポンス: {data}") from e


class OpenAICompatClient(_HTTPClient):
    """LM Studio (および llama.cpp server など OpenAI 互換API) 用。"""

    name = "LM Studio"
    hint = "LM Studio の Developer タブでサーバーを起動し、モデルを読み込んでください"

    def _base(self) -> str:
        return "" if self.host.endswith("/v1") else "/v1"

    def _resolve_model(self) -> str:
        if self.model:
            return self.model
        models = self._request(self._base() + "/models").get("data") or []
        if not models:
            raise LLMError("LM Studio にモデルが読み込まれていません。モデルをロードしてから実行してください")
        self.model = models[0]["id"]
        return self.model

    def chat(self, system: str, user: str, *, json_schema: dict[str, Any] | None = None,
             temperature: float = 0.4) -> str:
        payload: dict[str, Any] = {
            "model": self._resolve_model(),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
            "stream": False,
        }
        if json_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "video_prompt", "strict": True, "schema": json_schema},
            }
        data = self._request(self._base() + "/chat/completions", payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"想定外のレスポンス: {data}") from e


def make_client(backend: str = DEFAULT_BACKEND, host: str | None = None,
                model: str | None = None) -> _HTTPClient:
    if backend not in BACKENDS:
        raise ValueError(f"未知のバックエンド '{backend}'. 選択肢: {', '.join(BACKENDS)}")
    cls = OllamaClient if backend == "ollama" else OpenAICompatClient
    return cls(host or DEFAULT_HOSTS[backend],
               model or os.environ.get("VIDPROMPT_MODEL") or DEFAULT_MODELS[backend])
