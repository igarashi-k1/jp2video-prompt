import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from vidprompt.core import PROMPT_SCHEMA
from vidprompt.llm import LLMError, make_client


class FakeServer:
    """LM Studio (OpenAI互換) と Ollama の最小限のモック。"""

    def __init__(self, models=("qwen2.5-7b-instruct",)):
        self.requests = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def _json(self, obj):
                b = json.dumps(obj).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                outer.requests.append(("GET", self.path, None))
                self._json({"data": [{"id": m} for m in models]})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append(("POST", self.path, body))
                if self.path == "/api/chat":
                    self._json({"message": {"content": "ollama-ok"}})
                else:
                    self._json({"choices": [{"message": {"content": "lmstudio-ok"}}]})

            def log_message(self, *a):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class LLMTest(unittest.TestCase):
    def test_lmstudio_autoselects_loaded_model_and_sends_schema(self):
        s = FakeServer()
        try:
            c = make_client("lmstudio", s.url)
            self.assertEqual(c.chat("sys", "hi", json_schema=PROMPT_SCHEMA), "lmstudio-ok")
            self.assertEqual(s.requests[0][:2], ("GET", "/v1/models"))
            method, path, body = s.requests[1]
            self.assertEqual(path, "/v1/chat/completions")
            self.assertEqual(body["model"], "qwen2.5-7b-instruct")
            self.assertEqual(body["response_format"]["type"], "json_schema")
            self.assertEqual(body["response_format"]["json_schema"]["schema"], PROMPT_SCHEMA)
        finally:
            s.close()

    def test_lmstudio_host_with_v1_suffix(self):
        s = FakeServer()
        try:
            c = make_client("lmstudio", s.url + "/v1", "my-model")
            c.chat("sys", "hi")
            self.assertEqual(s.requests[0][1], "/v1/chat/completions")
            self.assertEqual(s.requests[0][2]["model"], "my-model")
            self.assertNotIn("response_format", s.requests[0][2])
        finally:
            s.close()

    def test_lmstudio_no_model_loaded(self):
        s = FakeServer(models=())
        try:
            with self.assertRaises(LLMError):
                make_client("lmstudio", s.url).chat("sys", "hi")
        finally:
            s.close()

    def test_ollama(self):
        s = FakeServer()
        try:
            self.assertEqual(make_client("ollama", s.url).chat("sys", "hi", json_schema={"a": 1}), "ollama-ok")
            self.assertEqual(s.requests[0][2]["model"], "qwen2.5:7b")
            self.assertEqual(s.requests[0][2]["format"], {"a": 1})
        finally:
            s.close()

    def test_unknown_backend(self):
        with self.assertRaises(ValueError):
            make_client("nope")


if __name__ == "__main__":
    unittest.main()
