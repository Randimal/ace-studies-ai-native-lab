"""Read local defaults without changing process environment or logging secrets."""
from dataclasses import dataclass, field
import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import SecretStr

from .providers import PROVIDERS
from .semantic import EMBEDDING_MODELS

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
KEY_NAMES = {"OpenAI": "OPENAI_API_KEY", "Google Gemini": "GOOGLE_API_KEY",
             "Groq": "GROQ_API_KEY", "Anthropic": "ANTHROPIC_API_KEY",
             "OpenRouter": "OPENROUTER_API_KEY"}
SETTING_NAMES = ("LLM_PROVIDER", "LLM_MODEL", "RETRIEVAL_MODE", "EMBEDDING_PROVIDER", "EMBEDDING_MODEL")


@dataclass
class Defaults:
    provider: str = "OpenAI"
    model: str = ""
    retrieval: str = "Lexical"
    embedding_provider: str = "OpenAI"
    embedding_model: str = "text-embedding-3-small"
    keys: dict[str, SecretStr] = field(default_factory=dict, repr=False)
    warnings: list[str] = field(default_factory=list)

    def key(self, provider):
        return self.keys.get(provider, SecretStr("")).get_secret_value()


def load_defaults(path=None, environ=None):
    """Environment wins over .env, including explicitly empty environment values.

    Never load .env.example or search parent folders. Disable interpolation so
    values are literal and cannot accidentally incorporate unrelated variables.
    """
    defaults = Defaults()
    path = ENV_FILE if path is None else path
    environ = os.environ if environ is None else environ
    try:
        file_values = dotenv_values(path, interpolate=False, encoding="utf-8-sig")
    except (OSError, UnicodeError):
        file_values = {}
        defaults.warnings.append("Could not read .env. Check its permissions and UTF-8 encoding.")
    values = {name: str(environ.get(name, file_values.get(name)) or "").strip()
              for name in (*SETTING_NAMES, *KEY_NAMES.values())}
    def choice(name, allowed, fallback):
        value = values[name]
        for option in allowed:
            if option.casefold() == value.casefold():
                return option
        if value:
            defaults.warnings.append(f"Unsupported {name}; using the built-in default. Check .env or your environment.")
        return fallback
    defaults.provider = choice("LLM_PROVIDER", PROVIDERS, "OpenAI")
    defaults.model = values["LLM_MODEL"][:150]
    mode = choice("RETRIEVAL_MODE", ["lexical", "semantic"], "lexical")
    defaults.retrieval = "Lexical" if mode == "lexical" else "Semantic — API embeddings"
    defaults.embedding_provider = choice("EMBEDDING_PROVIDER", EMBEDDING_MODELS, "OpenAI")
    defaults.embedding_model = values["EMBEDDING_MODEL"][:150] or EMBEDDING_MODELS[defaults.embedding_provider]
    defaults.keys = {provider: SecretStr(values[name]) for provider, name in KEY_NAMES.items()}
    return defaults
