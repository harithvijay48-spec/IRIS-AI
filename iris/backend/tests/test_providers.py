import unittest

from providers import ProviderError, parse_spec


class ProviderSpecTests(unittest.TestCase):
    def test_accepts_meta_model(self):
        self.assertEqual(parse_spec("meta:muse-spark-1.3"), ("meta", "muse-spark-1.3"))

    def test_accepts_existing_providers(self):
        self.assertEqual(parse_spec("gemini:gemini-2.5-flash"), ("gemini", "gemini-2.5-flash"))
        self.assertEqual(parse_spec("ollama:llama3.2"), ("ollama", "llama3.2"))

    def test_rejects_unknown_provider(self):
        with self.assertRaises(ProviderError):
            parse_spec("unknown:model")

    def test_rejects_missing_model(self):
        with self.assertRaises(ProviderError):
            parse_spec("meta:")


if __name__ == "__main__":
    unittest.main()

class MetaProviderTests(unittest.TestCase):
    def test_meta_requires_server_side_key(self):
        import asyncio
        import os
        from unittest.mock import patch
        from providers import call_meta

        with patch.dict(os.environ, {"MODEL_API_KEY": "", "META_API_KEY": ""}):
            with self.assertRaises(ProviderError):
                asyncio.run(call_meta("muse-spark-1.3", "system", "hello"))

    def test_meta_uses_bearer_auth_and_parses_completion(self):
        import asyncio
        import os
        from unittest.mock import patch
        import providers

        captured = {}

        class FakeResponse:
            status_code = 200

            @staticmethod
            def json():
                return {"choices": [{"message": {"content": "IRIS_OK"}}]}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def post(self, url, json, headers):
                captured.update(url=url, body=json, headers=headers)
                return FakeResponse()

        with patch.dict(os.environ, {"MODEL_API_KEY": "test-secret", "META_API_KEY": ""}):
            with patch.object(providers.httpx, "AsyncClient", return_value=FakeClient()):
                result = asyncio.run(providers.call_meta("muse-spark-1.3", "system", "hello"))

        self.assertEqual(result, ("IRIS_OK", []))
        self.assertEqual(captured["url"], "https://api.meta.ai/v1/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-secret")
        self.assertEqual(captured["body"]["model"], "muse-spark-1.3")
