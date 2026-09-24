import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx

from app.services.ai_service import AIService
from app.services.providers import (
    GroqProvider,
    OpenRouterProvider,
    ProviderConfigurationError,
    ProviderDisabledError,
    UnsupportedProviderError,
    create_provider,
)


def provider_config(**overrides):
    values = {
        "DEFAULT_PROVIDER": "openrouter",
        "ENABLED_PROVIDERS": "openrouter,groq",
        "OPENROUTER_API_KEY": "openrouter-test-key",
        "OPENROUTER_BASE_URL": "https://openrouter.test/v1",
        "OPENROUTER_MODEL": "openrouter/test-model",
        "GROQ_API_KEY": "groq-test-key",
        "GROQ_BASE_URL": "https://groq.test/v1",
        "GROQ_LLM_MODEL": "groq-test-model",
        "AI_REQUEST_TIMEOUT_SECONDS": 7,
        "AI_MAX_RETRIES": 2,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class ProviderFactoryTests(unittest.TestCase):
    def test_factory_selects_openrouter(self):
        provider = create_provider(config=provider_config())

        self.assertIsInstance(provider, OpenRouterProvider)
        self.assertEqual(provider.model, "openrouter/test-model")

    def test_factory_selects_groq(self):
        provider = create_provider("groq", provider_config())

        self.assertIsInstance(provider, GroqProvider)
        self.assertEqual(provider.model, "groq-test-model")

    def test_unsupported_provider_fails_clearly(self):
        with self.assertRaisesRegex(UnsupportedProviderError, "Unsupported AI provider"):
            create_provider("anthropic", provider_config())

    def test_disabled_provider_fails_clearly(self):
        config = provider_config(ENABLED_PROVIDERS="openrouter")

        with self.assertRaisesRegex(ProviderDisabledError, "disabled: groq"):
            create_provider("groq", config)

    def test_missing_api_key_fails_before_http_request(self):
        provider = create_provider("groq", provider_config(GROQ_API_KEY=""))

        with patch("app.services.providers.httpx.Client") as client:
            with self.assertRaisesRegex(ProviderConfigurationError, "missing its API key"):
                provider.chat("system", "user")

        client.assert_not_called()


class ProviderHTTPTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.client.__enter__ = Mock(return_value=self.client)
        self.client.__exit__ = Mock(return_value=None)
        self.response = Mock(status_code=200)
        self.response.json.return_value = {
            "choices": [{"message": {"content": "provider response"}}]
        }
        self.client.post.return_value = self.response

    def test_openrouter_request_uses_configured_url_and_model(self):
        provider = create_provider(config=provider_config())

        with patch("app.services.providers.httpx.Client", return_value=self.client) as client:
            result = provider.chat("system", "user")

        self.assertEqual(result, "provider response")
        client.assert_called_once_with(timeout=7)
        args, kwargs = self.client.post.call_args
        self.assertEqual(args[0], "https://openrouter.test/v1/chat/completions")
        self.assertEqual(kwargs["json"]["model"], "openrouter/test-model")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer openrouter-test-key")

    def test_groq_request_uses_configured_url_and_model(self):
        provider = create_provider("groq", provider_config())

        with patch("app.services.providers.httpx.Client", return_value=self.client):
            provider.chat("system", "user")

        args, kwargs = self.client.post.call_args
        self.assertEqual(args[0], "https://groq.test/v1/chat/completions")
        self.assertEqual(kwargs["json"]["model"], "groq-test-model")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer groq-test-key")

    def test_timeout_retry_configuration_is_applied(self):
        self.client.post.side_effect = [httpx.TimeoutException("timed out"), self.response]
        provider = create_provider(config=provider_config(AI_MAX_RETRIES=1))

        with patch("app.services.providers.httpx.Client", return_value=self.client) as client:
            result = provider.chat("system", "user")

        self.assertEqual(result, "provider response")
        client.assert_called_with(timeout=7)
        self.assertEqual(self.client.post.call_count, 2)


class AIServiceCompatibilityTests(unittest.TestCase):
    def test_provider_response_keeps_existing_evaluation_format(self):
        service = AIService.__new__(AIService)
        service.provider = SimpleNamespace(
            chat=lambda *args, **kwargs: (
                "SCORE: 8\n"
                "FEEDBACK: Clear explanation.\n"
                "MODEL_ANSWER: Use a hash map.\n"
                "FOLLOW_UP: What is the complexity?"
            )
        )

        result = service.evaluate_answer("Question", "Answer", "Engineer", "technical")

        self.assertEqual(result["score"], 8.0)
        self.assertEqual(result["feedback"], "Clear explanation.")
        self.assertEqual(result["model_answer"], "Use a hash map.")
        self.assertEqual(result["follow_up"], "What is the complexity?")


if __name__ == "__main__":
    unittest.main()
