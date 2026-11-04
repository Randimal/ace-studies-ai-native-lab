from tests.helpers import scripted_exam
from pathlib import Path
from streamlit.testing.v1 import AppTest
import pytest

APP = str(Path(__file__).parents[1] / "app.py")


def test_env_defaults_hidden_keys_overrides_and_reset(monkeypatch, tmp_path):
    from core import config
    from core.generation import ModelCalls
    from core.validation import ExamRequest
    path = tmp_path / ".env"
    path.write_text("LLM_PROVIDER=Groq\nLLM_MODEL=default-model\nGROQ_API_KEY=file-secret\n"
                    "EMBEDDING_PROVIDER=Google Gemini\nEMBEDDING_MODEL=embedding-test\n"
                    "GOOGLE_API_KEY=embedding-secret\nRETRIEVAL_MODE=semantic\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", path)
    keys = []
    def invoke(self, *args, **kwargs):
        keys.append(self.settings.api_key.get_secret_value())
        return scripted_exam(ExamRequest(count=1), [])
    monkeypatch.setattr(ModelCalls, "invoke", invoke)
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert app.selectbox(key="provider").value == "Groq"
    assert app.text_input(key="model_Groq").value == "default-model"
    assert app.checkbox(key="prepare_semantic").value is True
    assert app.selectbox(key="embedding_provider").value == "Google Gemini"
    assert app.text_input(key="embedding_model_Google Gemini").value == "embedding-test"
    assert app.text_input(key="key_Groq").value == ""
    assert app.text_input(key="embedding_key_Google Gemini").value == ""
    assert not app.checkbox(key="consent").value
    assert not app.checkbox(key="embedding_consent").value
    app.radio(key="source_mode").set_value("Topic only").run()
    app.button(key="prepare_material").click().run()
    app.text_input(key="topic").set_value("numbers")
    app.number_input(key="count").set_value(1)
    app.checkbox(key="consent").check()
    app.button(key="generate_exam").click().run()
    assert not app.error and keys == ["file-secret"]
    assert "file-secret" not in str(app.session_state["papers"])
    app.text_input(key="key_Groq").set_value("override-secret")
    app.text_input(key="model_Groq").set_value("override-model")
    app.button(key="generate_exam").click().run()
    assert keys[-1] == "override-secret"
    assert app.text_input(key="model_Groq").value == "override-model"
    app.button(key="clear_session").click().run()
    assert app.text_input(key="key_Groq").value == ""
    assert app.text_input(key="model_Groq").value == "default-model"
    app.selectbox(key="provider").set_value("OpenAI").run()
    assert app.text_input(key="model_OpenAI").value == ""
    assert app.text_input(key="key_OpenAI").value == ""


@pytest.fixture
def mocked_llm(monkeypatch):
    from core.generation import ModelCalls
    from core.validation import ExamRequest
    from langchain_core.documents import Document
    def invoke(self, schema, instruction, data, *args):
        kinds = data["question_types"]
        request = ExamRequest(count=data["count"], question_format=kinds[0] if len(set(kinds)) == 1 else "mixed")
        docs = [Document(page_content=s["text"], metadata={"source_id": s["source_id"]}) for s in data["sources"]]
        return scripted_exam(request, docs)
    monkeypatch.setattr(ModelCalls, "invoke", invoke)


def configured_app(prepare=True):
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.text_input(key="model_OpenAI").set_value("test-model")
    app.text_input(key="key_OpenAI").set_value("synthetic-key")
    app.checkbox(key="consent").check()
    if prepare:
        app.button(key="prepare_material").click().run()
    return app


def test_sample_generation_and_rerun(monkeypatch, mocked_llm):
    app = configured_app()
    assert not app.exception
    app.button(key="generate_exam").click().run()
    assert not app.exception and not app.error
    assert len(app.session_state["result"]["exam"].questions) == 5
    import core.graph
    monkeypatch.setattr(core.graph, "run_exam", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Unexpected regeneration")))
    app.run()
    assert not app.exception and not app.error
    assert len(app.get("download_button")) == 2


def test_mixed_attempt_submit_and_reset(monkeypatch, mocked_llm):
    app = configured_app()
    app.selectbox(key="question_format").set_value("Mixed question types")
    app.number_input(key="count").set_value(3)
    app.button(key="generate_exam").click().run()
    assert not app.exception and not app.error
    exam = app.session_state["result"]["exam"]
    attempt_id = app.session_state["attempt"]["exam_id"]
    assert not any("Answer and explanation" in e.label for e in app.expander)
    assert not any(b.label == "Download answer key" for b in app.get("download_button"))
    import core.graph
    with monkeypatch.context() as patch:
        patch.setattr(core.graph, "run_exam", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Unexpected AI call")))
        app.radio(key=f"response_{attempt_id}_q1").set_value(exam.questions[0].answer_index).run()
        for index in exam.questions[1].answer_indices:
            app.checkbox(key=f"response_{attempt_id}_q2_{index}").check().run()
        app.text_area(key=f"response_{attempt_id}_q3").set_value("My written answer").run()
        assert app.session_state["attempt"]["responses"]["q3"] == "My written answer"
        app.button(key="submit_exam").click().run()
        assert not app.exception
        assert app.session_state["attempt"]["grades"] == {"q1": "correct", "q2": "correct", "q3": "manual_review"}
        assert app.radio(key=f"response_{attempt_id}_q1").disabled
        assert any(b.label == "Download answer key" for b in app.get("download_button"))
    app.button(key="generate_exam").click().run()
    assert app.session_state["attempt"]["exam_id"] != attempt_id
    assert not app.session_state["attempt"]["submitted"]
    app.selectbox(key="selected_exam").set_value(attempt_id).run()
    assert app.session_state["attempt"]["submitted"]
    assert app.radio(key=f"response_{attempt_id}_q1").value == exam.questions[0].answer_index
    assert app.text_area(key=f"response_{attempt_id}_q3").value == "My written answer"
    app.button(key="clear_session").click().run()
    assert "attempt" not in app.session_state


def test_history_limit_reuse_and_failed_generation(monkeypatch, mocked_llm):
    from core import study_session
    from core.generation import ModelCalls
    from core.validation import LabError
    app = configured_app()
    monkeypatch.setattr(study_session, "load_text", lambda *a: pytest.fail("Material was parsed again"))
    app.selectbox(key="question_format").set_value("Short written answers")
    app.number_input(key="count").set_value(1)
    app.button(key="generate_exam").click().run()
    first_id = app.session_state["attempt"]["exam_id"]
    app.text_area(key=f"response_{first_id}_q1").set_value("Saved draft").run()
    app.button(key="generate_exam").click().run()
    second_id = app.session_state["attempt"]["exam_id"]
    app.selectbox(key="selected_exam").set_value(first_id).run()
    assert app.text_area(key=f"response_{first_id}_q1").value == "Saved draft"
    app.selectbox(key="selected_exam").set_value(second_id).run()
    assert app.text_area(key=f"response_{second_id}_q1").value == ""
    for _ in range(4):
        app.button(key="generate_exam").click().run()
    assert not app.exception and not app.error
    papers = app.session_state["papers"]
    assert len(papers) == 5 and [p["number"] for p in papers] == [2, 3, 4, 5, 6]
    assert first_id not in [p["attempt"]["exam_id"] for p in papers]
    assert f"response_{first_id}_q1" not in app.session_state
    selected = app.session_state["selected_exam"]
    def fail(*args, **kwargs):
        raise LabError("provider", "Provider unavailable.")
    monkeypatch.setattr(ModelCalls, "invoke", fail)
    app.button(key="generate_exam").click().run()
    assert app.error and not app.exception
    assert len(app.session_state["papers"]) == 5
    assert app.session_state["selected_exam"] == selected
    app.button(key="clear_session").click().run()
    assert "material" not in app.session_state and "papers" not in app.session_state


def test_generation_requires_prepared_material(mocked_llm):
    app = configured_app(prepare=False)
    app.button(key="generate_exam").click().run()
    assert app.error and "Prepare study material" in app.error[0].value
    assert "papers" not in app.session_state


def test_session_isolation_and_clear(mocked_llm):
    first = configured_app()
    first.button(key="generate_exam").click().run()
    second = AppTest.from_file(APP, default_timeout=30).run()
    assert "result" not in second.session_state
    first.button(key="clear_session").click().run()
    assert "result" not in first.session_state


def test_paste_and_topic_generation(notes, mocked_llm):
    app = configured_app(prepare=False)
    app.radio[0].set_value("Paste notes").run()
    app.text_area[0].set_value(notes)
    app.button(key="prepare_material").click().run()
    app.button(key="generate_exam").click().run()
    assert not app.exception and not app.error
    app = configured_app(prepare=False)
    app.radio[0].set_value("Topic only").run()
    app.button(key="prepare_material").click().run()
    app.text_input(key="topic").set_value("water")
    app.button(key="generate_exam").click().run()
    assert not app.error and not app.exception
    assert app.session_state["result"]["basis"] == "model knowledge"


def test_generation_requires_credentials_and_consent(monkeypatch):
    from core.generation import ModelCalls
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: pytest.fail("Unexpected model call"))
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert app.selectbox(key="provider").options == ["OpenAI", "Google Gemini", "Groq", "Anthropic", "OpenRouter"]
    app.button(key="generate_exam").click().run()
    assert app.error and "Confirm" in app.error[0].value
    app.checkbox(key="consent").check()
    app.text_input(key="model_OpenAI").set_value("test-model")
    app.button(key="prepare_material").click().run()
    app.button(key="generate_exam").click().run()
    assert app.error and "API key" in app.error[0].value
    assert "result" not in app.session_state


def test_topic_provider_flow_and_key_isolation(monkeypatch):
    from core.generation import ModelCalls
    from core.validation import Exam, Question
    captured_keys = []
    def invoke(self, *args, **kwargs):
        captured_keys.append(self.settings.api_key.get_secret_value())
        return Exam(questions=[Question(question="Which number is even?", options=["1", "2", "3", "5"],
                                       answer_index=1, explanation="Two is divisible by two.")])
    monkeypatch.setattr(ModelCalls, "invoke", invoke)
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.selectbox[0].set_value("Groq").run()
    app.text_input(key="model_Groq").set_value("test-model")
    app.text_input(key="key_Groq").set_value("session-only-test-key")
    app.radio[0].set_value("Topic only").run()
    app.button(key="prepare_material").click().run()
    app.text_input(key="topic").set_value("numbers")
    app.number_input[0].set_value(1)
    app.checkbox(key="consent").check()
    app.button(key="generate_exam").click().run()
    assert not app.exception and not app.error
    assert captured_keys == ["session-only-test-key"]
    assert "session-only-test-key" not in str(app.session_state["result"])
    other = AppTest.from_file(APP, default_timeout=30).run()
    other.selectbox[0].set_value("Groq").run()
    assert other.text_input(key="key_Groq").value == ""


def test_semantic_consent_and_index_reuse(monkeypatch, notes):
    from types import SimpleNamespace
    from core import semantic
    from core.documents import load_text
    from core.generation import ModelCalls
    from core.validation import ExamRequest
    events = []
    monkeypatch.setenv("OPENAI_API_KEY", "default-embedding-key")
    def factory(*args):
        assert args[0].api_key.get_secret_value() == "default-embedding-key"
        def embed(texts):
            events.append("documents")
            return [[1., 0.] for _ in texts]
        return SimpleNamespace(embed_documents=embed, embed_query=lambda text: [1., 0.])
    monkeypatch.setattr(semantic, "create_embeddings", factory)
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: scripted_exam(ExamRequest(count=5), load_text(notes)))
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.selectbox(key="provider").set_value("Groq").run()
    app.text_input(key="model_Groq").set_value("test-model")
    app.text_input(key="key_Groq").set_value("generation-key")
    app.checkbox(key="prepare_semantic").check().run()
    assert app.text_input(key="embedding_key_OpenAI").value == ""
    app.text_input(key="topic").set_value("water vapor")
    app.checkbox(key="consent").check()
    app.button(key="prepare_material").click().run()
    assert app.error and not events
    assert "material" not in app.session_state
    app.checkbox(key="embedding_consent").check()
    app.button(key="prepare_material").click().run()
    assert not app.error and events == ["documents"]
    assert "papers" not in app.session_state
    app.button(key="generate_exam").click().run()
    assert not app.error and not app.exception
    assert app.session_state["result"]["retrieval"] == "semantic"
    app.button(key="generate_exam").click().run()
    assert not app.error and events == ["documents"]
    assert app.session_state["result"]["embedding_cache_hit"]
    app.button(key="clear_session").click().run()
    assert "vector_index" not in app.session_state


@pytest.mark.parametrize("delete_button", ["delete_vector_index", "clear_session"])
def test_chroma_persistence_opt_in_and_delete(monkeypatch, notes, tmp_path, delete_button):
    from types import SimpleNamespace
    from core import semantic, vector_db
    from core.documents import load_text
    from core.generation import ModelCalls
    from core.validation import ExamRequest
    monkeypatch.setattr(vector_db, "DATABASE_PATH", tmp_path)
    monkeypatch.setattr(semantic, "create_embeddings", lambda *a: SimpleNamespace(
        embed_documents=lambda texts: [[1., 0.] for _ in texts], embed_query=lambda text: [1., 0.]))
    monkeypatch.setattr(ModelCalls, "invoke", lambda *a, **k: scripted_exam(ExamRequest(count=5), load_text(notes)))
    app = AppTest.from_file(APP, default_timeout=45).run()
    app.selectbox(key="provider").set_value("Groq").run()
    app.text_input(key="model_Groq").set_value("test-model")
    app.text_input(key="key_Groq").set_value("generation-key")
    app.checkbox(key="prepare_semantic").check().run()
    assert app.checkbox(key="persist_index").value is False
    app.checkbox(key="persist_index").check().run()
    app.text_input(key="embedding_key_OpenAI").set_value("embedding-key")
    app.text_input(key="topic").set_value("water vapor")
    app.checkbox(key="embedding_consent").check()
    app.checkbox(key="consent").check()
    app.button(key="prepare_material").click().run()
    app.button(key="generate_exam").click().run()
    assert not app.exception and not app.error
    store = app.session_state["vector_index"]["store"]
    assert store.persistent
    name = store.name
    other = store.client.create_collection("unrelated-collection", embedding_function=None)
    app.button(key=delete_button).click().run()
    assert not app.exception and not app.error
    if delete_button == "clear_session":
        assert "vector_index" not in app.session_state
        assert "material" not in app.session_state
        assert "papers" not in app.session_state
    else:
        assert not app.session_state["vector_index"]
        assert not app.session_state["material"]["semantic_ready"]
        assert app.session_state["papers"]
    assert store.client.get_collection(other.name, embedding_function=None).name == other.name
    with pytest.raises(Exception):
        store.client.get_collection(name, embedding_function=None)
