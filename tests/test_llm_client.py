import io
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

from verdict_desk import llm

KEY = "test-key-123"


class FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def reply(content, finish="stop"):
    return FakeResponse({"choices": [{"message": {"content": content}, "finish_reason": finish}]})


def http_error(code, body=b"", retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("https://api.mistral.ai/v1/chat/completions", code, "err", headers, io.BytesIO(body))


class ClientTest(unittest.TestCase):
    def setUp(self):
        for patch in (
            mock.patch.dict(os.environ, {"MISTRAL_API_KEY": KEY}),
            mock.patch.object(llm, "BASE_URL", "https://api.mistral.ai/v1"),
            mock.patch.object(llm, "MIN_INTERVAL", 0.0),
            mock.patch.object(llm, "_next_start", 0.0),
        ):
            patch.start()
            self.addCleanup(patch.stop)
        pause = mock.patch.object(llm, "_pause")
        self.pause = pause.start()
        self.addCleanup(pause.stop)

    def test_available_follows_the_key(self):
        self.assertTrue(llm.available())
        with mock.patch.dict(os.environ, {"MISTRAL_API_KEY": "  \n"}):
            self.assertFalse(llm.available())
        with mock.patch.dict(os.environ):
            del os.environ["MISTRAL_API_KEY"]
            self.assertFalse(llm.available())

    def test_request_shape_and_text(self):
        with mock.patch("urllib.request.urlopen", return_value=reply("hello")) as urlopen:
            self.assertEqual(llm.chat("be brief", "hi"), "hello")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.mistral.ai/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {KEY}")
        body = json.loads(request.data)
        self.assertEqual(body["model"], llm.MODEL)
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(body["max_tokens"], llm.MAX_TOKENS)
        self.assertEqual(body["messages"], [{"role": "system", "content": "be brief"}, {"role": "user", "content": "hi"}])

    def test_max_tokens_override_reaches_the_request(self):
        with mock.patch("urllib.request.urlopen", return_value=reply("ok")) as urlopen:
            llm.chat("s", "u", max_tokens=6000)
            llm.chat("s", "u")
        sent = [json.loads(call.args[0].data)["max_tokens"] for call in urlopen.call_args_list]
        self.assertEqual(sent, [6000, llm.MAX_TOKENS])

    def test_key_is_trimmed(self):
        with mock.patch.dict(os.environ, {"MISTRAL_API_KEY": f"{KEY}\n"}):
            with mock.patch("urllib.request.urlopen", return_value=reply("ok")) as urlopen:
                llm.chat("s", "u")
        self.assertEqual(urlopen.call_args.args[0].get_header("Authorization"), f"Bearer {KEY}")

    def test_block_content_keeps_only_the_text_blocks(self):
        blocks = [{"type": "thinking", "thinking": [{"type": "text", "text": "hidden"}]}, {"type": "text", "text": "answer"}]
        with mock.patch("urllib.request.urlopen", return_value=reply(blocks)):
            self.assertEqual(llm.chat("s", "u"), "answer")

    def test_empty_content_names_the_finish_reason(self):
        with mock.patch("urllib.request.urlopen", return_value=reply("", finish="length")):
            with self.assertRaisesRegex(ValueError, "length"):
                llm.chat("s", "u")

    def test_unexpected_shape_is_a_value_error(self):
        for payload in ({"choices": []}, {"error": "x"}, {"choices": "x"}):
            with mock.patch("urllib.request.urlopen", return_value=FakeResponse(payload)):
                with self.assertRaises(ValueError):
                    llm.chat("s", "u")

    def test_429_waits_for_retry_after_then_succeeds(self):
        with mock.patch("urllib.request.urlopen", side_effect=[http_error(429, retry_after=3), reply("done")]):
            self.assertEqual(llm.chat("s", "u"), "done")
        self.pause.assert_called_once_with(3.0)

    def test_429_without_retry_after_backs_off(self):
        with mock.patch("urllib.request.urlopen", side_effect=[http_error(429), http_error(503), reply("done")]):
            self.assertEqual(llm.chat("s", "u"), "done")
        self.assertEqual([c.args[0] for c in self.pause.call_args_list], [2.0, 4.0])

    def test_gives_up_after_the_retry_budget(self):
        errors = [http_error(429, b'{"message":"rate limit"}') for _ in range(llm.MAX_RETRIES + 1)]
        with mock.patch("urllib.request.urlopen", side_effect=errors) as urlopen:
            with self.assertRaisesRegex(llm.LLMError, "429"):
                llm.chat("s", "u")
        self.assertEqual(urlopen.call_count, llm.MAX_RETRIES + 1)

    def test_401_is_not_retried_and_the_error_never_carries_the_key(self):
        body = f'{{"detail":"Invalid API Key {KEY}"}}'.encode()
        with mock.patch("urllib.request.urlopen", side_effect=[http_error(401, body)]) as urlopen:
            with self.assertRaises(llm.LLMError) as caught:
                llm.chat("s", "u")
        message = str(caught.exception)
        self.assertIn(f"HTTP 401 err from https://api.mistral.ai/v1 model {llm.MODEL}:", message)  # formato que vai para o ledger
        self.assertIn("Invalid API Key", message)
        self.assertNotIn(KEY, message)
        self.assertEqual(urlopen.call_count, 1)
        self.assertIsInstance(caught.exception, OSError)  # os `except OSError` do dossie e da narrativa continuam valendo

    def test_malformed_key_is_rejected_without_echoing_it(self):
        with mock.patch.dict(os.environ, {"MISTRAL_API_KEY": "abc\ndef ghi"}):
            with mock.patch("urllib.request.urlopen") as urlopen:
                with self.assertRaises(llm.LLMError) as caught:
                    llm.chat("s", "u")
        self.assertNotIn("abc", str(caught.exception))
        urlopen.assert_not_called()

    def test_missing_key_is_a_clear_error(self):
        with mock.patch.dict(os.environ):
            del os.environ["MISTRAL_API_KEY"]
            with self.assertRaisesRegex(llm.LLMError, "not set"):
                llm.chat("s", "u")

    def test_call_starts_are_spaced_even_across_threads(self):
        with mock.patch.object(llm, "MIN_INTERVAL", 0.5):
            threads = [threading.Thread(target=llm._wait_turn) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        waits = sorted(c.args[0] for c in self.pause.call_args_list)
        self.assertEqual(len(waits), 3)  # a primeira chamada nao espera
        for earlier, later in zip(waits, waits[1:]):
            self.assertAlmostEqual(later - earlier, 0.5, delta=0.05)

    def test_numeric_env_falls_back_when_invalid_or_empty(self):
        with mock.patch.dict(os.environ, {"X_NUM": "abc"}):
            self.assertEqual(llm._number("X_NUM", 7, int), 7)
        with mock.patch.dict(os.environ, {"X_NUM": ""}):
            self.assertEqual(llm._number("X_NUM", 1.5, float), 1.5)
        with mock.patch.dict(os.environ, {"X_NUM": "9"}):
            self.assertEqual(llm._number("X_NUM", 7, int), 9)


class LocalServerTest(unittest.TestCase):
    """Caminho real de HTTP (socket, cabecalhos, corpo de erro) contra um servidor local que imita a Mistral."""

    def test_429_then_200_over_a_real_socket(self):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                size = int(self.headers.get("Content-Length", 0))
                seen.append((self.path, self.headers.get("Authorization"), json.loads(self.rfile.read(size))))
                if len(seen) == 1:
                    payload, status = b'{"message":"rate limit"}', 429
                else:
                    payload, status = json.dumps({"choices": [{"message": {"content": "from server"}, "finish_reason": "stop"}]}).encode(), 200
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                if status == 429:
                    self.send_header("Retry-After", "2")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with mock.patch.dict(os.environ, {"MISTRAL_API_KEY": KEY}), mock.patch.object(llm, "BASE_URL", f"http://127.0.0.1:{server.server_port}/v1"), mock.patch.object(
            llm, "MIN_INTERVAL", 0.0
        ), mock.patch.object(llm, "_pause") as pause, mock.patch("urllib.request.urlopen", side_effect=opener.open):
            self.assertEqual(llm.chat("sys", "usr"), "from server")
        pause.assert_called_once_with(2.0)
        self.assertEqual([s[0] for s in seen], ["/v1/chat/completions"] * 2)
        self.assertEqual({s[1] for s in seen}, {f"Bearer {KEY}"})
        self.assertEqual(seen[1][2]["messages"][1], {"role": "user", "content": "usr"})


if __name__ == "__main__":
    unittest.main()
