
"""Groq implementation of the RU-P DraftClient interface."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.data.draft_rup import DraftClientError, DraftConfigurationError


GROQ_CHAT_COMPLETIONS_URL = (
    "https://api.groq.com/openai/v1/chat/completions"
)
SYSTEM_MESSAGE = (
    "Return only a valid JSON object with exactly two keys: "
    '"question" and "options". Follow the user transliteration '
    "instructions exactly. Do not add explanations or Markdown."
)

class GroqDraftClient:
    """Minimal Groq chat-completions client for RU-P drafting."""

    def __init__(
        self,
        api_key_env: str = "GROQ_API_KEY",
        timeout_s: float = 60.0,
    ) -> None:
        if not api_key_env or not api_key_env.strip():
            raise DraftConfigurationError("API key environment name is empty.")

        if timeout_s <= 0:
            raise DraftConfigurationError("Timeout must be positive.")

        self.api_key_env = api_key_env
        self.timeout_s = timeout_s

    def complete(self, prompt: str, model_string: str) -> str:
        """Send one chat-completion request and return its text content."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise DraftConfigurationError("Prompt must be non-empty text.")

        if not isinstance(model_string, str) or not model_string.strip():
            raise DraftConfigurationError("Model string must be non-empty.")

        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise DraftConfigurationError(
                f"Required environment variable {self.api_key_env} is not set."
            )

        payload = {
            "model": model_string,
            "temperature": 0,
            "max_completion_tokens": 4096,
            "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
        }

        body = json.dumps(payload).encode("utf-8")
        request = Request(
            GROQ_CHAT_COMPLETIONS_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_s) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )

        except HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                raise DraftClientError(
                    f"Temporary Groq HTTP error: {exc.code}"
                ) from None

            raise DraftConfigurationError(
                f"Groq rejected the request with HTTP {exc.code}."
            ) from None

        except (URLError, TimeoutError, OSError):
            raise DraftClientError(
                "Groq request failed due to a network or timeout error."
            ) from None

        except (UnicodeDecodeError, json.JSONDecodeError):
            raise DraftClientError(
                "Groq returned an invalid JSON response."
            ) from None

        try:
            content = response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise DraftClientError(
                "Groq response did not contain message content."
            ) from None

        if not isinstance(content, str):
            raise DraftClientError(
                "Groq message content was not text."
            )

        return content
