"""A small LangChain factory. Keys are arguments, never process configuration."""
from dataclasses import dataclass, field
import re

from pydantic import SecretStr
from .validation import LabError

PROVIDERS = ("OpenAI", "Google Gemini", "Groq", "Anthropic")


@dataclass(frozen=True)
class ProviderSettings:
    provider: str = "OpenAI"
    model: str = ""
    api_key: SecretStr = field(default_factory=lambda: SecretStr(""), repr=False)

    def __post_init__(self):
        if self.provider not in PROVIDERS:
            raise LabError("configuration", "Choose a supported provider.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,149}", self.model):
            raise LabError("configuration", "Enter a model ID available in your provider account.")
        if not isinstance(self.api_key, SecretStr) or not self.api_key.get_secret_value().strip():
            raise LabError("configuration", "Enter your API key for this session.")


def create_model(settings: ProviderSettings, timeout: float, output_tokens: int):
    """SDK retries are disabled: the graph owns the total retry budget.

    Explicit endpoints prevent common SDK environment URL overrides. No model
    catalog or entitlement is inferred from successful client construction.
    """
    key = settings.api_key.get_secret_value()
    common = dict(model=settings.model, api_key=key, max_retries=0,
                  timeout=timeout, max_tokens=output_tokens, cache=False, callbacks=[])
    if settings.provider == "OpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(**common, base_url="https://api.openai.com/v1")
    if settings.provider == "Groq":
        from langchain_groq import ChatGroq
        return ChatGroq(**common)
    if settings.provider == "Anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(**common, base_url="https://api.anthropic.com")
    if settings.provider == "Google Gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(**common, vertexai=False,
                                     base_url="https://generativelanguage.googleapis.com/")
    raise LabError("configuration", "Choose a supported provider.")
