from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.config import Settings, settings


class AIProviderError(RuntimeError):
    """Base error for configured provider failures."""


class UnsupportedProviderError(AIProviderError):
    pass


class ProviderDisabledError(AIProviderError):
    pass


class ProviderConfigurationError(AIProviderError):
    pass


class ProviderTimeoutError(AIProviderError):
    pass


class ProviderRequestError(AIProviderError):
    pass


class ProviderResponseError(AIProviderError):
    pass


class AIProvider(Protocol):
    name: str
    model: str

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        ...


@dataclass
class HTTPChatProvider:
    name: str
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int
    max_retries: int

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        self._validate_configuration()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(
                        f"{self.base_url.rstrip('/')}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    continue
                raise ProviderTimeoutError(
                    f"{self.name} request timed out after {self.timeout_seconds} seconds"
                ) from exc
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    continue
                raise ProviderRequestError(f"{self.name} request failed") from exc

            if response.status_code >= 500 and attempt < self.max_retries:
                continue
            if response.status_code >= 400:
                raise ProviderRequestError(
                    f"{self.name} request failed with status {response.status_code}"
                )
            return self._extract_content(response)

        raise ProviderRequestError(f"{self.name} request failed")

    def _validate_configuration(self) -> None:
        if not self.api_key.strip():
            raise ProviderConfigurationError(
                f"{self.name} provider is missing its API key"
            )
        if not self.base_url.strip():
            raise ProviderConfigurationError(
                f"{self.name} provider is missing its base URL"
            )
        if not self.model.strip():
            raise ProviderConfigurationError(
                f"{self.name} provider is missing its model"
            )

    def _extract_content(self, response: httpx.Response) -> str:
        try:
            data: dict[str, Any] = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(
                f"{self.name} returned an invalid chat response"
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError(
                f"{self.name} returned an empty chat response"
            )
        return content.strip()


class OpenRouterProvider(HTTPChatProvider):
    def __init__(self, config: Settings):
        super().__init__(
            name="openrouter",
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
            model=config.OPENROUTER_MODEL,
            timeout_seconds=config.AI_REQUEST_TIMEOUT_SECONDS,
            max_retries=config.AI_MAX_RETRIES,
        )


class GroqProvider(HTTPChatProvider):
    def __init__(self, config: Settings):
        super().__init__(
            name="groq",
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
            model=config.GROQ_LLM_MODEL,
            timeout_seconds=config.AI_REQUEST_TIMEOUT_SECONDS,
            max_retries=config.AI_MAX_RETRIES,
        )


def create_provider(
    provider_name: str | None = None,
    config: Settings | None = None,
) -> AIProvider:
    config = config or settings
    selected = (provider_name or config.DEFAULT_PROVIDER).strip().lower()
    enabled = {
        provider.strip().lower()
        for provider in config.ENABLED_PROVIDERS.split(",")
        if provider.strip()
    }
    providers = {
        "openrouter": OpenRouterProvider,
        "groq": GroqProvider,
    }

    if selected not in providers:
        raise UnsupportedProviderError(
            f"Unsupported AI provider: {selected}"
        )
    if selected not in enabled:
        raise ProviderDisabledError(
            f"AI provider is disabled: {selected}"
        )
    return providers[selected](config)
