# Ace Studies AI-Native Lab · Public v0.1

A local, educational exam generator for the **AI-Native Engineering** LinkedIn
series. Upload a text-based PDF or UTF-8 TXT, paste notes, or enter a topic. Create
1–10 single-answer, multiple-answer or short written questions.
Download separate printable exam and answer-key HTML files; use your browser to
print or save as PDF.

## Try an interactive exam

1. Start the app using the commands below. Choose an LLM provider, enter an
   available model ID and API key, and select **Sample** or your own study material.
   Optionally enable **Prepare semantic search (API embeddings)** in Study material.
   Click **Prepare study material** once to extract and chunk locally, and, when
   enabled, embed chunks through the selected API and store them in local Chroma.
   Upload multiple PDF/TXT files together if needed.
2. Choose **Mixed question types** and at least **3** questions, confirm the
   provider-sharing notice, then Generate. Generation uses the API and may cost money.
3. Answer using radio buttons (one option), checkboxes (all correct options), or
   a text area (short written response).
4. Click **Submit exam**. Answers lock and feedback becomes visible. Each choice
   question is worth one point; multiple-answer marking requires the exact set,
   with no partial credit. Blanks earn no point. Written answers remain for human
   review and are excluded from the automatic score. The rubric and sample answer
   help a reviewer; this version has no manual-score entry screen.
5. Download the paper, responses (JSON), or the answer key after submission.

Responses are temporary **Streamlit session state**, separate from Chroma. Normal
widget reruns preserve them; browser reloads, lost sessions or server restarts may
lose them. **Open a previous exam** restores a retained paper and its answers.
The latest **five papers** are kept; a successful sixth generation removes the
oldest paper and its answers, even if unfinished. A failed generation does not
remove any paper. Clear session removes all papers and prepared material.
Responses are not sent to an AI provider or written to disk by the app. Downloaded
backups contain your answers and question text. They can be read outside the app;
importing a backup is not implemented. This is a local learning tool, not a secure
exam platform: answer-key visibility is a UI convenience, not an access boundary.

New to the code? Start with [the beginner walkthrough](docs/LEARNING_GUIDE.md).

This is an independent reference implementation, not a production SaaS or a
release of a commercial platform. Publication ownership review is still pending.

## Quick start

Install **Python 3.11**. From the project directory, in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open http://127.0.0.1:8501. Configure a provider, model ID and API key, then select
**Sample** and the **Deterministic** workflow for your first run. Review the sharing
notice, click **Prepare study material**, then **Generate exam**. All question generation requires an LLM;
the sample is study material, not an offline generation mode. Difficulty is
requested, not verified.

Existing users: activate your project environment and install `requirements.txt`
again if dependencies are missing. Current local verification uses `.venv`;
older verification records refer to the previous `.venv-v01` environment.

No Docker, Node.js, database server, or separate backend is required. Generation
requires an account and API access with your chosen LLM provider.
Runtime and transitive versions are pinned in `requirements.txt`; direct
dependencies are listed in `requirements.in`. Some libraries bring internal web
server dependencies; no separate FastAPI application is maintained or launched.

## Use your own provider

Choose OpenAI, Google Gemini, Groq or Anthropic. Enter an exact model ID available
in your provider account and your key in the masked field. The integrations accept
model IDs rather than imposing a stale model catalog. Client construction and
mocked tests do not prove that a model is available or compatible. **Live tests of
the new integrations remain pending for all providers.** API usage may cost money.

For local defaults, copy `.env.example` to `.env` without overwriting an existing
file, then fill in your provider, model, retrieval and embedding settings and keys.
The app reads only the project-root `.env`. UI overrides take priority over
process environment variables, which take priority over `.env` and built-in defaults.
An explicitly empty environment variable overrides the corresponding `.env` value.
Unsupported provider/retrieval choices show a warning and fall back to defaults.

`LLM_MODEL` applies only to `LLM_PROVIDER`; `EMBEDDING_MODEL` applies only to
`EMBEDDING_PROVIDER`. Switching providers does not reuse a different provider's
model or key. The same provider key can serve generation and embeddings; the
embedding UI also allows an independent session override.

Default keys are never prefilled into password fields. A **Default key available**
caption indicates they can be used; leave the override blank to use them. Keys are
passed explicitly to each client, not written back to disk or process variables.
Typed overrides remain session-only. Clear session reloads settings and clears
overrides, but defaults remain available from the file/environment. After editing
`.env`, use Clear session to reapply setting defaults (this also removes papers).
Restart the app to pick up changes to its process environment. This is not secure
memory erasure. Default keys are server-wide configuration, intended for local use.
`.env` remains Git-ignored; never publish it or put real keys in `.env.example`.

Confirm the sharing notice before generation: your topic and selected source
passages go to the chosen provider, whose retention policies apply. Topic-only
generation is labelled **model knowledge**, without fabricated source citations.

## How it works

`app.py` handles only interface/session concerns. `core/` works without Streamlit.

- **LangChain:** Document objects with stable chunk/page metadata, lexical selection
  of these documents, ChatPromptTemplate, provider chat models, and typed JSON
  output through PydanticOutputParser. Complete JSON is required before parsing;
  structural validation is always local. Native schema enforcement is not assumed.
- **LangGraph deterministic workflow:** prepare → retrieve (documents only) →
  generate → validate → finish, with bounded retries on invalid/transient output.
- **LangGraph experimental workflow:** an LLM chooses permitted retrieve, generate,
  validate, revise and finish actions. State and conditional edges are explicit.
  Finishing always requires deterministic validation. This is a single agent with
  bounded local functions, not a multi-agent system. Live end-to-end verification
  remains pending.

Both workflows require the requested count and question types, four distinct
options for choice questions, valid answer indices, a rubric for written questions,
explanations, no normalized duplicate questions, and valid source IDs in
document mode. An explicit insufficient-evidence response stops generation.
These checks do **not** prove that the correct answer follows from the source or
that a question has only one semantically correct option. Review the content.

## Retrieval: lexical or semantic

One session uses one prepared document collection. Upload/select material once,
then generate more papers with different topics, counts, formats or difficulty.
Extraction and chunking are reused. With semantic preparation enabled, the vector
index is built by **Prepare study material** and reused by later exams; queries
still need query embeddings and each generated exam still calls the LLM. Clear
session starts a new collection. Saved Chroma indexes do not save exam history.

Text is normalized and split using LangChain's `RecursiveCharacterTextSplitter`,
with a maximum of **1,200 characters** and a **200-character target overlap**.
Paragraph and line breaks are retained; splitting tries paragraphs, then lines,
spaces and individual characters. Overlap can be smaller at natural boundaries.
Each PDF page is split independently so citations keep their page reference.
These are character counts, not token counts; chunking runs locally without an API.

Chunks carry a shared source ID, document-content identity, page, sequence number,
content hash and versioned chunking settings. Lexical and semantic retrieval use
the same chunks; this also prepares their IDs for a later hybrid retriever. A
focus topic selects chunks by lexical word overlap; no topic samples across the
document. The selected passages are included in the prompt. This is retrieval-
augmented generation. **Lexical** remains the default and makes no embedding API
calls. **Semantic — API embeddings** uses embedded Chroma with cosine similarity.
Chroma runs inside the application; no separate database server is needed.
Topic-only generation has no retrieval. Both retrieval options use an LLM to
generate the final questions.

For semantic retrieval, select **OpenAI** (default embedding model:
`text-embedding-3-small`) or **Google Gemini** (`gemini-embedding-001`), then supply
an embedding API key and confirm the separate sharing notice. Model IDs are
editable; live verification remains pending. Embedding providers and generation
providers are independent: Groq generation can use Gemini or OpenAI embeddings.
If both providers match, you can explicitly reuse the generation key. Groq (the
existing integration) and xAI Grok are distinct services; xAI is not implemented.

Semantic preparation sends **all chunks** to the embedding provider after consent.
Later semantic searches embed only the query. Generation sends retrieved passages to its provider.
API charges may apply. With no topic, coverage sampling makes no query embedding calls;
an agent may subsequently choose a query. Similarity selects nearest passages, not
proof of relevance or factual support. No silent lexical fallback hides failures.

By default, the session owns a temporary Chroma collection. Clear session deletes
it; restarting the server loses temporary collections. Clear the session to change
documents or embedding settings, then prepare again. Queries are re-embedded.

To retain an index, enable **Save the Chroma index on this computer** before
preparation. This explicitly saves source text, vectors and metadata in
`.local/chroma` (Git-ignored, not encrypted). After preparation, expand **Chroma
vector database** and keep its index ID. To reuse it after a restart, provide the
same document and embedding provider/model, enable saving, and enter the ID in
**Saved index ID**. This skips document embedding, but still embeds the query.
The database stores no API key, client or credential fingerprint.

Indexes saved with the older custom chunker are incompatible with the new chunk
identity. Leave **Saved index ID** blank to build a new index. Changing chunking
settings also invalidates reuse; rebuilding embeddings may incur API charges.

**Clear session deletes the active collection, including a saved index.** It leaves
other collections untouched. **Delete this vector index** removes only the index
and keeps papers available with lexical retrieval. Closing the browser or restarting
does not delete disk-saved collections. Deletion
is logical database deletion, not guaranteed secure erasure. Index IDs are not an
authentication mechanism. Embedded Chroma is intended here for local use, not
multi-user hosting. Temporary collections are isolated by random collection names.

Embedding calls have a separate ceiling of 32 requests and 600,000 UTF-8 input
bytes per run, with batches of at most 8 chunks / 12,000 bytes. SDK retries are
disabled. They share the workflow's cooperative deadline. Embedding request counts
are shown separately from generation/controller calls; costs are not estimated.

Provider references: [OpenAI embeddings](https://developers.openai.com/api/docs/guides/embeddings)
and [Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings).
Storage: [Chroma Python client](https://docs.trychroma.com/reference/python).

The interface displays cited passages and PDF page numbers. Retrieval coverage is
bounded and may omit relevant material; lexical search does not understand
synonyms. Source IDs prove traceability, not factual correctness.

## Limits and privacy

- 10 MiB uploads, 50 PDF pages, 100,000 extracted/input characters; UTF-8 TXT only.
- A collection accepts up to 10 files, 10 MiB combined, at most 50 nonempty PDF
  pages across unique documents and 100,000 prepared chunk characters including
  overlap. Identical documents are deduplicated. Each individual PDF also has
  the 50-page limit, including blank pages.
- At most five papers per session, ten questions per paper and 5,000 characters
  per written response. Inactive response widgets are released; attempt data is
  retained only while its paper remains in history. These bounds limit stored
  application content, not the memory consumption of the entire Python process.
- PDF extraction runs in a killable child process with a 15-second timeout and
  no saved document. Linux adds a parser memory limit; Windows does not.
- At most 3 generation attempts, 12 total LLM calls and 12 agent decisions per run.
- 120-second cooperative workflow deadline; provider operation timeout at most
  30 seconds. In-flight work can overrun before the next check; late results fail.
- 100,000 conservative budget units (UTF-8 prompt bytes plus requested output
  tokens), not tokenizer-measured usage. Unknown model context limits may reject
  requests. Output ceilings are 4096 for exams and 1024 for decisions.
- No global application retrieval cache, graph checkpointer, external tracing, or
  automatic generation on widget/download reruns. SDK retries are disabled.
  Chroma manages process-local collections; anonymized telemetry is disabled and
  supplied API vectors avoid Chroma's default embedding model downloads.
- Downloaded HTML is escaped and contains no credentials or execution traces.
  Exam papers exclude answer indices and teacher explanations. Downloads do
  contain user-requested generated content; handle them accordingly.

Scanned/encrypted PDFs, OCR, authentication and persistent exam/history storage
are out of scope. Difficulty is requested, not verified. Topic-only facts may be
wrong. The default server binds to localhost; unrestricted public hosting needs a
separate security and abuse-control review.

## Tests and examples

If PDF preparation fails, the app now explains whether the file is encrypted,
exceeds page/text limits, has no extractable text, or could not be parsed. Export
an unencrypted/repaired copy, use a smaller chapter, or extract text with an OCR
tool as appropriate. The 10 MiB upload allowance does not remove the 50-page or
100,000-character limits. A debugger warning in subprocess stderr is separate
from the worker's JSON error response; raw stderr is not shown to users.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip check
python tools/check_release.py
```

Tests block provider network access and use scripted responses. They exercise real
LangGraph routing and Streamlit's AppTest without paid APIs. Try the bundled sample
first, then pasted notes, TXT/PDF uploads, and a topic with a configured provider.
Only an explicit Generate click makes calls; results retain their original labels.

## History and release status

The Part 2 article's 6/15 deterministic versus 0/15 agentic pilot belongs to the old
implementation. Historical evaluation files remain unchanged under `evaluation/`;
see `docs/historical/README.md`. They are not new public v0.1 measurements.

This simplified public v0.1 starts a new release line. See `CHANGELOG.md`,
`docs/CHANGE_REPORT.md`, `docs/VERIFICATION.md`, and `docs/PROVENANCE.md` for changes,
verification boundaries, and unresolved publication review. Future work includes
live provider verification and human factual/educational evaluation.

MIT license retained, subject to confirming ownership and attribution. Do not
contribute secrets, proprietary code, private prompts, or course materials without
redistribution rights.
