"""Streamlit owns UI/session state; core contains no Streamlit imports."""
from pathlib import Path

import streamlit as st
from pydantic import SecretStr, ValidationError

from core.attempts import grade_attempt, export_responses
from core.study_session import prepare_material, add_paper, MAX_PAPERS
from core.export import export_html
from core.graph import run_exam
from core.providers import PROVIDERS, ProviderSettings
from core.semantic import EMBEDDING_MODELS, EmbeddingSettings, SemanticRetriever
from core.validation import ExamRequest, LabError
from core.vector_db import clear_index
from core.config import load_defaults
from core.adaptive import topic_map, plan_practice, record_submission

st.set_page_config(page_title="Ace Studies · Exam Lab", page_icon="📚", layout="centered")


def clear_session():
    try:
        clear_index(st.session_state.get("vector_index", {}), delete_saved=True)
    except LabError as error:
        st.error(str(error))
        return
    for key in list(st.session_state):
        del st.session_state[key]


def delete_vector_index():
    try:
        clear_index(st.session_state.get("vector_index", {}), delete_saved=True)
        st.session_state["resume_index_id"] = ""
        st.session_state.pop("prepared_embedding_settings", None)
        if "material" in st.session_state:
            st.session_state["material"]["semantic_ready"] = False
        st.session_state["retrieval"] = "Lexical"
        st.session_state["vector_deleted"] = True
    except LabError as error:
        st.error(str(error))


st.title("Ace Studies · Exam Lab")
st.write("Turn study material into an interactive or printable exam. A local learning lab for AI-native engineering.")
st.button("Clear session", key="clear_session", on_click=clear_session,
          help="Start again with new documents. Removes temporary papers, answers and chunks; also deletes this session's active Chroma collection, including saved indexes.")

defaults = load_defaults()
for warning in defaults.warnings:
    st.warning(warning)
st.session_state.setdefault("provider", defaults.provider)
st.session_state.setdefault("retrieval", defaults.retrieval)
st.session_state.setdefault("embedding_provider", defaults.embedding_provider)
provider = st.selectbox("Provider", PROVIDERS, key="provider")
st.caption("Generation requires an LLM provider and API key. Enter an exact model ID available in your account. Live integration verification is pending.")
st.session_state.setdefault(f"model_{provider}", defaults.model if provider == defaults.provider else "")
model = st.text_input("Model ID", max_chars=150, key=f"model_{provider}")
if provider == "OpenRouter":
    st.caption("Use an OpenRouter model ID (author/model), or openrouter/free for its free chat router. "
               "Free routes have usage limits; other models may be paid. Requests pass through OpenRouter to its model providers.")
key_override = st.text_input("API key override — this session only", type="password", key=f"key_{provider}",
                             help="Leave blank to use this provider's environment or .env key.")
api_key = key_override.strip() or defaults.key(provider)
if defaults.key(provider):
    st.caption("Default key available. Enter an override above only if needed.")
st.caption("Settings start from environment/.env defaults. Clear session reloads setting defaults and removes session overrides; default keys remain available.")

# Material and embedding configuration are fixed together at preparation time.
material = st.session_state.get("material")
with st.container(border=True):
    st.subheader("Study material")
    if material is None:
        source_mode = st.radio("Source", ["Sample", "Paste notes", "Upload PDF / TXT", "Topic only"], horizontal=True, key="source_mode")
        text, uploads = "", []
        if source_mode == "Sample":
            text = (Path(__file__).parent / "examples" / "study_notes.txt").read_text(encoding="utf-8")
            with st.expander("View sample notes"):
                st.text(text)
        elif source_mode == "Paste notes":
            text = st.text_area("Notes", height=200, max_chars=100_000, key="notes")
        elif source_mode == "Upload PDF / TXT":
            uploads = st.file_uploader("PDF / TXT files · up to 10 files, 10 MiB combined", type=["pdf", "txt"],
                                       accept_multiple_files=True, key="upload")
        else:
            st.warning("Topic-only exams use model knowledge, not supplied document evidence.")
        use_embeddings = False
        embedding_consent = False
        persist_index, resume_index_id = False, ""
        if source_mode != "Topic only":
            use_embeddings = st.checkbox("Prepare semantic search (API embeddings)",
                                         value=defaults.retrieval.startswith("Semantic"), key="prepare_semantic")
            st.caption("Enable this to embed and store the chunks during preparation. Leave it off for local lexical search only.")
            if use_embeddings:
                embedding_provider = st.selectbox("Embedding provider", list(EMBEDDING_MODELS), key="embedding_provider")
                st.session_state.setdefault(f"embedding_model_{embedding_provider}",
                    defaults.embedding_model if embedding_provider == defaults.embedding_provider else EMBEDDING_MODELS[embedding_provider])
                embedding_model = st.text_input("Embedding model ID", max_chars=150, key=f"embedding_model_{embedding_provider}")
                if embedding_provider == "OpenRouter":
                    st.caption("Choose an embedding model, not a chat model. Free availability and limits can change. "
                               "Requests pass through OpenRouter to its model providers.")
                    if embedding_model.strip() == "nvidia/nemotron-3-embed-1b:free":
                        st.warning("NVIDIA's free endpoint logs inputs for security and product improvement. "
                                   "Do not send confidential or personal data. "
                                   "[Review model terms](https://openrouter.ai/nvidia/nemotron-3-embed-1b:free).")
                reuse_key = provider == embedding_provider and st.checkbox("Use my generation API key for embeddings", value=True, key="reuse_embedding_key")
                if reuse_key:
                    embedding_key = api_key
                else:
                    embedding_override = st.text_input("Embedding API key override — this session only", type="password", key=f"embedding_key_{embedding_provider}",
                                                      help="Leave blank to use the embedding provider's environment or .env key.")
                    embedding_key = embedding_override.strip() or defaults.key(embedding_provider)
                    if defaults.key(embedding_provider):
                        st.caption("Default embedding key available.")
                embedding_consent = st.checkbox("I agree to send all document chunks and retrieval queries to the embedding provider. API charges may apply.", key="embedding_consent")
                persist_index = st.checkbox("Save the Chroma index on this computer", key="persist_index")
                if persist_index:
                    st.warning("Document text, embeddings and metadata are stored in .local/chroma without encryption. Clear session deletes the active collection. Closing the browser or restarting alone does not delete saved data.")
                    resume_index_id = st.text_input("Saved index ID (optional; leave blank for a new index)", max_chars=36, key="resume_index_id")
                else:
                    st.caption("Chroma stores the collection in memory. Clear session deletes it; server restart also removes it.")
        if st.button("Prepare study material", key="prepare_material"):
            try:
                if use_embeddings and not embedding_consent:
                    raise LabError("consent", "Confirm the embedding-sharing notice before preparing material.")
                with st.spinner("Extracting, chunking and preparing the search index…"):
                    candidate = prepare_material(source_mode, text=text, uploads=[(u.name, u.getvalue()) for u in uploads])
                    candidate["semantic_ready"] = False
                    if use_embeddings:
                        embedding_settings = EmbeddingSettings(embedding_provider, embedding_model.strip(), SecretStr(embedding_key))
                        cache = st.session_state.setdefault("vector_index", {})
                        search = SemanticRetriever(embedding_settings, cache, persistent=persist_index, resume_id=resume_index_id)
                        search.prepare(candidate["documents"])
                        candidate.update(semantic_ready=True, embedding_provider=embedding_provider,
                                         embedding_model=embedding_model.strip(), embedding_calls=search.calls,
                                         persistent=persist_index, resume_id=resume_index_id)
                        # Credentials remain separate from material, history and exports.
                        st.session_state["prepared_embedding_settings"] = embedding_settings
                    st.session_state["material"] = candidate
                    st.session_state["retrieval"] = "Semantic — API embeddings" if use_embeddings else "Lexical"
                st.rerun()
            except LabError as error:
                st.error(str(error))
            except Exception:
                st.error("Study material could not be prepared. Check the files, embedding configuration and installed dependencies.")
    else:
        source_mode = material["mode"]
        st.success("Study material ready: " + (", ".join(material["names"]) or "Topic-only session"))
        st.caption(f"{len(material['documents'])} prepared chunks. Clear session to change material or embedding settings.")
        if material.get("semantic_ready"):
            st.caption(f"Indexed with {material['embedding_provider']} / {material['embedding_model']} · Preparation embedding requests: {material['embedding_calls']}")
        elif source_mode != "Topic only":
            st.caption("Lexical search only. To enable semantic search, clear this session and prepare with embeddings enabled.")

st.subheader("Exam generation")
with st.expander("Adaptive practice · learning topics"):
    st.caption("Before your first exam, enter up to 20 learning topics, one per line, using your study material's headings. "
               "These names stay fixed for this session. For example: Conditional probability, Bayes theorem. "
               "Automatic topic discovery is not included.")
    topic_text = st.text_area("Learning topics (one per line)", key="learning_topics_text", max_chars=2020,
                             disabled=bool(st.session_state.get("papers")))
    profile = st.session_state.get("learning_profile", {})
    if profile:
        st.dataframe([{"Topic": t, **s, "Evidence": "Limited" if s["correct"] + s["incorrect"] < 2 else "Practice results"}
                      for t, s in profile.items()], hide_index=True)
    st.caption("Only submitted choice questions update performance. Written answers are excluded; skipped questions are tracked separately. "
               "Totals survive the five-paper history limit and are removed by Clear session.")
adaptive_mode = st.checkbox("Practice my weak areas", key="adaptive_mode")
retrieval_mode = "Lexical"
if material and source_mode != "Topic only":
    modes = ["Lexical", "Semantic — API embeddings"] if material.get("semantic_ready") else ["Lexical"]
    retrieval_mode = st.selectbox("Retrieval", modes, key="retrieval")
    st.caption("Retrieval can change per exam. A blank focus topic selects document-wide coverage without a query embedding.")

topic = st.text_input("Topic" if source_mode == "Topic only" else "Focus topic (optional)", max_chars=200, key="topic")
left, right = st.columns(2)
count = left.number_input("Number of questions", min_value=1, max_value=10, value=2, key="count")
difficulty = right.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Mixed"], index=1, key="difficulty")
formats = {"Single answer (radio buttons)": "single", "Multiple answers (checkboxes)": "multiple",
           "Short written answers": "written", "Mixed question types": "mixed"}
question_format = st.selectbox("Question format", list(formats), key="question_format")
st.caption("Mixed cycles through single, multiple and written questions. Choose at least 3 questions to try all three. Written answers need manual review.")
workflow = st.selectbox("Workflow", ["Deterministic", "Agentic — experimental"], key="workflow")
if workflow.startswith("Agentic"):
    st.caption("An LLM chooses the next permitted action. Calls, decisions, retries and execution time are bounded. Live end-to-end verification is pending.")

consent = st.checkbox("I understand that my topic and selected source passages will be sent to the chosen LLM provider, whose policies apply.", key="consent")

# Only this button starts exam generation. Paper selection and answer edits reuse
# history entries, each carrying its original evidence/workflow labels.
if st.button("Generate exam", key="generate_exam", type="primary"):
    try:
        if not consent:
            raise LabError("consent", "Confirm the provider-sharing notice before generating.")
        if material is None:
            raise LabError("input", "Prepare study material before generating an exam.")
        with st.spinner("Generating your exam from prepared material…"):
            documents = material["documents"]
            topics = topic_map(topic_text)
            practice_topics, practice_reason = [], "Normal exam without topic tracking."
            if topics or adaptive_mode:
                practice_topics, practice_reason = plan_practice(topics, st.session_state.get("learning_profile", {}), count, adaptive_mode)
            previous_questions = [q.question for p in st.session_state.get("papers", [])
                                  for q in p["result"]["exam"].questions][-20:] if adaptive_mode else []
            request = ExamRequest(count=count, difficulty=difficulty, topic=topic, question_format=formats[question_format],
                                  practice_topics=practice_topics, previous_questions=previous_questions,
                                  workflow="agentic" if workflow.startswith("Agentic") else "deterministic")
            settings = ProviderSettings(provider, model.strip(), SecretStr(api_key))
            semantic = None
            if retrieval_mode.startswith("Semantic"):
                embedding_settings = st.session_state["prepared_embedding_settings"]
                cache = st.session_state.get("vector_index", {})
                semantic = SemanticRetriever(embedding_settings, cache, persistent=material["persistent"],
                                             resume_id=material["resume_id"], prepared_only=True)
            result = run_exam(request, documents, settings, semantic=semantic)
            result["practice_reason"] = practice_reason
            result["practice_topics"] = practice_topics
            history = st.session_state.setdefault("papers", [])
            number = st.session_state.get("paper_number", 0) + 1
            paper, removed = add_paper(history, result, request, provider, model.strip(), number)
            st.session_state["paper_number"] = number
            st.session_state["selected_exam"] = paper["attempt"]["exam_id"]
            if removed:
                st.info(f"Paper {removed['number']} and its answers were removed to keep the latest {MAX_PAPERS} papers.")
    except LabError as error:
        st.error(str(error))
    except ValidationError:
        st.error("Check the topic, question count, model, and difficulty settings.")
    except Exception:
        st.error("The exam could not be generated. Check your inputs and installed dependencies. No raw provider details are displayed.")

history = st.session_state.get("papers", [])
if history:
    st.subheader("Your exam papers")
    st.caption(f"Keeping the latest {MAX_PAPERS} papers in this session. A successful sixth generation removes the oldest, including its answers. Download papers and responses you want to keep.")
    by_id = {p["attempt"]["exam_id"]: p for p in history}
    selected = st.selectbox("Open a previous exam", list(reversed(by_id)), key="selected_exam",
                            format_func=lambda value: f"Paper {by_id[value]['number']} · {by_id[value]['request']['topic'] or 'Whole document'} · {by_id[value]['request']['count']} questions")
    paper = by_id[selected]
    # References only: history owns the result and attempt, not duplicate copies.
    result = st.session_state["result"] = paper["result"]
    st.info(result.get("practice_reason", "Normal exam."))
    if result.get("practice_topics"):
        st.caption("Question topics: " + " · ".join(result["practice_topics"]))
    attempt = st.session_state["attempt"] = paper["attempt"]
    st.caption(f"{paper['provider']} · {paper['model']} · {paper['request']['difficulty']} · {paper['request']['question_format']}")
    # Streamlit discards hidden widgets. Answers live separately in each attempt;
    # restore widgets from that data when returning to a paper, and drop stale keys.
    prefix = f"response_{selected}_"
    for key in list(st.session_state):
        if key.startswith("response_") and not key.startswith(prefix):
            del st.session_state[key]
    st.caption(f"Evidence: {result['basis']} · Workflow: {result['workflow']} · Model calls: {result['model_calls']}")
    st.caption(f"Retrieval: {result['retrieval']} · Embedding requests this run: {result['embedding_calls']}")
    st.warning("AI answers can be wrong. Source references and structural validation do not establish factual correctness.")
    exam = result["exam"]
    attempt = st.session_state["attempt"]
    st.info("Answers are kept only in this session. Reloading, disconnecting or restarting may lose them. The latest five papers and their answers are retained. Download responses for a backup.")
    st.caption("Submit when ready; blank answers are allowed. Multiple-answer questions earn one point only when every correct option and no extra option is selected. Written answers are not automatically scored.")
    for number, question in enumerate(exam.questions, 1):
        st.text(f"{number}. {question.question}")
        qid = f"q{number}"
        widget_key = f"response_{attempt['exam_id']}_{qid}"
        saved = attempt["responses"].get(qid)
        if question.kind == "single":
            st.session_state.setdefault(widget_key, saved)
            response = st.radio("Select one answer", list(range(4)), index=None,
                                format_func=lambda i, q=question: f"{chr(65+i)}. {q.options[i]}",
                                key=widget_key, disabled=attempt["submitted"])
        elif question.kind == "multiple":
            st.caption("Select all correct answers")
            for i in range(4):
                st.session_state.setdefault(f"{widget_key}_{i}", i in (saved or []))
            response = [i for i, option in enumerate(question.options) if st.checkbox(
                f"{chr(65+i)}. {option}", key=f"{widget_key}_{i}", disabled=attempt["submitted"])]
        else:
            st.session_state.setdefault(widget_key, saved or "")
            response = st.text_area("Your written answer", max_chars=5000, key=widget_key,
                                    disabled=attempt["submitted"])
        if not attempt["submitted"]:
            attempt["responses"][qid] = response
    if not attempt["submitted"] and st.button("Submit exam", key="submit_exam", type="primary"):
        attempt["grades"] = grade_attempt(exam, attempt["responses"])
        attempt["submitted"] = True
        record_submission(st.session_state.setdefault("learning_profile", {}), exam, attempt, topic_map(topic_text))
        st.rerun()
    if attempt["submitted"]:
        total = sum(q.kind != "written" for q in exam.questions)
        score = sum(value == "correct" for value in attempt["grades"].values())
        st.subheader("Your results")
        st.write(f"Automatically marked questions: {score}/{total}. Written answers are excluded." if total else "This exam has only written questions; no automatic score is assigned.")
        labels = {"correct": "Correct", "incorrect": "Incorrect", "unanswered": "Unanswered", "manual_review": "Needs manual review"}
        for number, question in enumerate(exam.questions, 1):
            st.write(f"Question {number}: {labels[attempt['grades'][f'q{number}']]}")
            with st.expander(f"Answer and explanation · Question {number}"):
                indices = [question.answer_index] if question.kind == "single" else question.answer_indices
                for index in indices:
                    st.text(f"{chr(65 + index)}. {question.options[index]}")
                if question.kind == "written":
                    st.text("Review rubric: " + question.rubric)
                st.text(question.explanation)
                for source in result["sources"]:
                    if source.metadata["source_id"] in question.source_ids:
                        st.caption(f"{source.metadata.get('source_name', 'Study material')} · {source.metadata['source_id']} · Page {source.metadata['page'] or 'n/a'}")
                        st.text(source.page_content)
    left, right = st.columns(2)
    left.download_button("Download exam", export_html(exam, basis=result["basis"]),
                         file_name="exam.html", mime="text/html", on_click="ignore")
    if attempt["submitted"]:
        right.download_button("Download answer key", export_html(exam, answer_key=True, basis=result["basis"]),
                              file_name="answer-key.html", mime="text/html", on_click="ignore")
    st.download_button("Download responses (JSON)", export_responses(exam, attempt),
                       file_name="responses.json", mime="application/json", on_click="ignore")
    st.caption("Open either HTML file in a browser and print or save as PDF. Downloads intentionally contain the generated exam content.")
    with st.expander("Learning view: executed nodes"):
        st.text(" → ".join(result["trace"]))

index_cache = st.session_state.get("vector_index", {})
if "store" in index_cache:
    store = index_cache["store"]
    with st.expander("Chroma vector database"):
        st.caption("Saved on disk" if store.persistent else "Session memory only")
        st.code(store.name, language=None)
        if store.persistent:
            st.caption("Keep this ID to resume with the same document and embedding provider/model. An index ID is not authentication. This application is for local use.")
        st.button("Delete this vector index", key="delete_vector_index", on_click=delete_vector_index)
if st.session_state.pop("vector_deleted", False):
    st.success("Index deleted from Chroma. Previously downloaded files are unaffected.")

st.caption("Educational local application. No authentication or abuse controls for unrestricted public hosting.")
