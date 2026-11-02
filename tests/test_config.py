import os

from core.config import load_defaults


def test_file_defaults_and_environment_precedence(tmp_path):
    path = tmp_path / ".env"
    path.write_text("LLM_PROVIDER=Groq\nLLM_MODEL=file-model\nRETRIEVAL_MODE=semantic\n"
                    "EMBEDDING_PROVIDER=Google Gemini\nEMBEDDING_MODEL=embedding-test\n"
                    "GROQ_API_KEY=file-secret\nGOOGLE_API_KEY=embedding-secret\n", encoding="utf-8")
    before = dict(os.environ)
    defaults = load_defaults(path, {"LLM_MODEL": "environment-model", "GROQ_API_KEY": "environment-secret"})
    assert defaults.provider == "Groq" and defaults.model == "environment-model"
    assert defaults.retrieval == "Semantic — API embeddings"
    assert defaults.embedding_provider == "Google Gemini" and defaults.embedding_model == "embedding-test"
    assert defaults.key("Groq") == "environment-secret"
    assert defaults.key("Google Gemini") == "embedding-secret"
    assert "secret" not in repr(defaults)
    assert dict(os.environ) == before
    assert load_defaults(path, {"GROQ_API_KEY": ""}).key("Groq") == ""


def test_missing_invalid_and_literal_defaults(tmp_path):
    missing = load_defaults(tmp_path / "missing.env", {})
    assert missing.provider == "OpenAI" and not missing.key("OpenAI")
    path = tmp_path / ".env"
    path.write_text("LLM_PROVIDER=private-invalid-value\nRETRIEVAL_MODE=hybrid\n"
                    "EMBEDDING_PROVIDER=other\nOPENAI_API_KEY=${DO_NOT_EXPAND}\n", encoding="utf-8")
    defaults = load_defaults(path, {})
    assert defaults.provider == "OpenAI" and defaults.retrieval == "Lexical"
    assert len(defaults.warnings) == 3
    assert "private-invalid-value" not in str(defaults.warnings)
    assert defaults.key("OpenAI") == "${DO_NOT_EXPAND}"
