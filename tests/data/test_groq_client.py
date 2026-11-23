
import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from src.data.groq_client import GroqDraftClient
from src.data.draft_rup import (
    DraftClientError,
    DraftConfigurationError,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class GroqClientTests(unittest.TestCase):

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-test-key"})
    @patch("src.data.groq_client.urlopen")
    def test_successful_mock_request(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({
            "choices": [
                {"message": {"content": '{"question":"test","options":[]}' }}
            ]
        })

        client = GroqDraftClient()
        result = client.complete("test prompt", "openai/gpt-oss-120b")

        self.assertEqual(
            result,
            '{"question":"test","options":[]}'
        )

        request = mock_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(payload["model"], "openai/gpt-oss-120b")
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertEqual(
            payload["response_format"]["type"],
            "json_object",
        )
        self.assertEqual(
            request.get_header("Authorization"),
            "Bearer fake-test-key",
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch("src.data.groq_client.urlopen")
    def test_missing_api_key(self, mock_urlopen):
        client = GroqDraftClient()

        with self.assertRaises(DraftConfigurationError):
            client.complete("prompt", "openai/gpt-oss-120b")

        mock_urlopen.assert_not_called()

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-test-key"})
    @patch("src.data.groq_client.urlopen")
    def test_rate_limit_is_retryable(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            "https://api.groq.com",
            429,
            "Rate limited",
            {},
            BytesIO(b""),
        )

        client = GroqDraftClient()

        with self.assertRaises(DraftClientError):
            client.complete("prompt", "openai/gpt-oss-120b")

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-test-key"})
    @patch("src.data.groq_client.urlopen")
    def test_auth_error_is_not_retryable(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            "https://api.groq.com",
            401,
            "Unauthorized",
            {},
            BytesIO(b""),
        )

        client = GroqDraftClient()

        with self.assertRaises(DraftConfigurationError):
            client.complete("prompt", "openai/gpt-oss-120b")

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-test-key"})
    @patch("src.data.groq_client.urlopen")
    def test_invalid_response_is_rejected(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({
            "unexpected": "structure"
        })

        client = GroqDraftClient()

        with self.assertRaises(DraftClientError):
            client.complete("prompt", "openai/gpt-oss-120b")


if __name__ == "__main__":
    unittest.main()
