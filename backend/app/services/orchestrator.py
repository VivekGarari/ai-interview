from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ProviderConfig:
    name: str
    enabled: bool = False
    priority: int = 0


@dataclass
class AIOrchestrator:
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        defaults = {
            "groq": ProviderConfig(name="groq", enabled=True, priority=100),
            "openai": ProviderConfig(name="openai", enabled=False, priority=90),
            "anthropic": ProviderConfig(name="anthropic", enabled=False, priority=80),
            "deepseek": ProviderConfig(name="deepseek", enabled=False, priority=70),
        }
        self.providers = {**defaults, **self.providers}

    def select_provider(self, task_type: str, capabilities: Dict[str, bool] | None = None) -> str:
        capabilities = capabilities or {}
        if task_type == "reasoning" and capabilities.get("openai"):
            return "openai"
        if task_type == "coding" and capabilities.get("groq"):
            return "groq"
        if task_type == "long_context" and capabilities.get("anthropic"):
            return "anthropic"
        if capabilities.get("deepseek"):
            return "deepseek"
        for name, config in sorted(self.providers.items(), key=lambda item: item[1].priority, reverse=True):
            if config.enabled:
                return name
        return "groq"

    def get_capabilities(self) -> Dict[str, List[str]]:
        return {
            "llm": ["groq", "openai", "anthropic", "deepseek"],
            "search": ["tavily", "brave", "exa"],
            "memory": ["postgresql", "redis", "qdrant"],
            "automation": ["github", "gmail", "slack", "jira"],
        }
