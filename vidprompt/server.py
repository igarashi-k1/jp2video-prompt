"""標準ライブラリだけで動くローカル Web UI。127.0.0.1 のみで待ち受けます。"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

from .core import ChatModel, generate
from .llm import LLMError
from .targets import TARGETS


def make_handler(model: ChatModel):
    page = resources.files("vidprompt").joinpath("static/index.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def do_GET(self):
            if self.path == "/":
                self._send(200, page, "text/html; charset=utf-8")
            elif self.path == "/api/targets":
                self._json(200, [{"key": t.key, "label": t.label} for t in TARGETS.values()])
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/api/generate":
                return self._json(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length) or b"{}")
                r = generate(
                    model, req.get("text", ""), req.get("target", "generic"),
                    duration=int(req["duration"]) if req.get("duration") else None,
                    aspect=req.get("aspect") or None,
                    style_hint=req.get("style") or None,
                )
                self._json(200, r.to_dict())
            except LLMError as e:
                self._json(502, {"error": str(e)})
            except (ValueError, json.JSONDecodeError) as e:
                self._json(400, {"error": str(e)})

        def log_message(self, fmt, *args):
            pass

    return Handler


def serve(model: ChatModel, host: str = "127.0.0.1", port: int = 7860) -> None:
    httpd = ThreadingHTTPServer((host, port), make_handler(model))
    print(f"Web UI: http://{host}:{port}  (Ctrl+C で終了)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
