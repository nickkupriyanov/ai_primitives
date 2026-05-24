# Document QA / RAG — Design Spec

## Overview

Четвёртый модуль AI Primitives Playground: **Document QA** — вопрос-ответ по пользовательским документам с citations и отслеживанием retrieval failure cases.

Backend: FastAPI + ChromaDB (embedded vector DB) + OpenAI embeddings (`text-embedding-3-small`).  
Frontend: Next.js + React 19 + Tailwind v4 + shadcn/ui.

---

## Architecture

### Backend

```
backend/app/
├── routes/
│   └── documents.py          # POST /documents/ingest, POST /documents/query,
│                             # GET /documents/sources, DELETE /documents/sources/{id},
│                             # POST /documents/demo/{scenario}
├── services/
│   ├── embedding_service.py  # OpenAI embeddings API wrapper + batching
│   ├── document_service.py   # Chunking (sliding window), ingest, retrieval + LLM answer generation
│   └── chroma_client.py      # Singleton wrapper over ChromaDB: collection init, add, query, delete
├── schemas.py                # + SourceCreate, SourceOut, QuestionRequest, QuestionResponse,
│                             #   CitationOut, FailureCaseOut
├── data/
│   ├── chroma/               # Persisted ChromaDB storage (.gitignored)
│   └── demo/                 # Pre-baked demo documents: conspectus/*.md, project-docs/*.md,
│       │                     # compare/*.md, faq/*.md
│       └── failures.json     # Predefined failure cases per scenario
└── tests/
    └── test_documents.py     # Tests for all endpoints + embedding mock
```

#### New Dependencies (`requirements.txt`)
```
chromadb>=0.5.0
tiktoken>=0.7.0
PyPDF2>=3.0.0
```

#### Data Flow

1. **Ingest**  
   Upload (`SourceCreate`) → chunk with sliding window (500 tokens, 100 overlap) → embed each chunk via OpenAI → store in ChromaDB with metadata (`source_id`, `filename`, `chunk_position`, `text`).

2. **Query**  
   Question → embed question → ChromaDB similarity search (top-k=5) → retrieved chunks as context → LLM prompt: «Answer based on context, cite sources» → response + `CitationOut[]`.

3. **Demo scenarios**  
   POST `/documents/demo/{scenario}` — loads documents from `data/demo/` directory, ingests them, returns `SourceOut[]`. Scenario names: `conspectus`, `project-docs`, `compare`, `faq`.

4. **Failure cases**  
   Hardcoded in `data/demo/failures.json`. Returned inline with `QuestionResponse` when the question matches a known demo question. Format: expected vs actual answer + reason.

---

### Frontend

```
frontend/app/
├── document-qa/
│   ├── page.tsx              # Main page with two tabs
│   └── actions.ts            # Server actions: uploadDocument, queryDocument,
│                             #   getSources, deleteSource, loadDemoScenario
└── components/
    └── document-qa/
        ├── DemoScenarios.tsx       # 4 demo cards, each with "Load" button + predefined questions
        ├── DocumentUploader.tsx    # Tabs: file upload (.md/.txt/.pdf) | text paste | demo scenario
        ├── SourcesList.tsx         # Loaded document list with chunk counts, delete button
        ├── QuestionInput.tsx       # Text input + submit, disabled if no sources loaded
        ├── AnswerCard.tsx          # Answer text + inline citation badges
        ├── CitationBadge.tsx       # Clickable citation: shows chunk text on hover/click
        └── FailureCasesPanel.tsx   # Table: question, expected, actual, retrieval issue
```

#### Page Layout — Two Tabs

**Tab 1: Demo Scenarios** (default)

4 scenario cards:
- **Спроси по конспектам** — 3 Python конспекта (синтаксис, ООП, async), 3 predefined questions
- **Спроси по документации проекта** — ROADMAP.md + README, questions about project architecture
- **Сравни 3 документа и найди противоречия** — 3 docs with deliberate contradictions
- **Собери FAQ из набора заметок** — Q&A-style notes, "Generate FAQ from these notes"

Each card: title, description, "Load Scenario" button → ingest demo docs → show predefined questions → user clicks one → AnswerCard with citations + FailureCasesPanel.

**Tab 2: My Documents**

- DocumentUploader (left/top) — file input (accepts `.md`, `.txt`, `.pdf`) + text paste textarea
- SourcesList — list of ingested docs with chunk count and delete
- QuestionInput — text field + submit
- AnswerCard — with citations
- No failure cases for custom documents

---

## Data Models (Pydantic — added to `schemas.py`)

```python
from datetime import datetime


class SourceCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: Literal["text/plain", "text/markdown", "application/pdf"]
    content: str = Field(..., min_length=1, max_length=500_000)


class SourceOut(BaseModel):
    id: str
    filename: str
    content_type: str
    chunk_count: int
    created_at: datetime


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4_000)
    source_ids: list[str] | None = None  # filter, None = all
    top_k: int = Field(default=5, ge=1, le=20)


class CitationOut(BaseModel):
    source_id: str
    source_filename: str
    chunk_position: int
    chunk_text: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationOut]
    latency_ms: int
    failure_case: FailureCaseOut | None = None


class FailureCaseOut(BaseModel):
    question: str
    expected_answer: str
    actual_answer: str
    retrieval_issue: str  # e.g. "wrong chunk", "missing key fragment"
```

---

## API Endpoints

| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| `POST` | `/documents/ingest` | `SourceCreate` | `SourceOut` |
| `POST` | `/documents/query` | `QuestionRequest` | `QuestionResponse` |
| `GET` | `/documents/sources` | — | `list[SourceOut]` |
| `DELETE` | `/documents/sources/{source_id}` | — | `{"deleted": true}` |
| `POST` | `/documents/demo/{scenario}` | — | `list[SourceOut]` |

---

## Chunking Strategy

- **Tokenizer**: `tiktoken` (`cl100k_base` for `text-embedding-3-small`)
- **Chunk size**: 500 tokens
- **Overlap**: 100 tokens (sliding window)
- **Split logic**:
  - Markdown: split on `##` headers → then paragraphs (`\n\n`)
  - Plain text: split on `\n\n`
  - PDF: extract text via `PyPDF2` → treat as plain text
- **Metadata per chunk**: `source_id`, `filename`, `chunk_position` (0-based index), `text`

---

## ChromaDB Setup

- **Embedding function**: `OpenAIEmbeddingFunction` with `text-embedding-3-small` via OpenAI client
- **Collection name**: `"documents"` (single collection)
- **Persistence**: `backend/app/data/chroma/` (`.gitignored`)
- **Distance metric**: cosine (default)
- **Client**: Singleton `ChromaClient` wrapper in `chroma_client.py`

---

## Demo Documents

Located in `backend/app/data/demo/`:

```
demo/
├── conspectus/
│   ├── python-basics.md       # Variables, types, control flow
│   ├── python-oop.md          # Classes, inheritance, dunder methods
│   └── python-async.md        # async/await, event loop
├── project-docs/
│   ├── roadmap.md             # Copy of ROADMAP.md
│   └── architecture.md        # Brief architecture overview of AI Primitives
├── compare/
│   ├── doc-a.md               # "Python uses dynamic typing"
│   ├── doc-b.md               # "Python has optional static typing via TypeVar" (contradiction)
│   └── doc-c.md               # "Python is purely interpreted" (contradiction with JIT/compilation)
├── faq/
│   ├── notes-1.md             # Q&A about FastAPI
│   └── notes-2.md             # Q&A about Next.js
└── failures.json              # Predefined failure cases
```

### `failures.json` structure

```json
[
  {
    "scenario": "conspectus",
    "question": "Как работает GIL в Python?",
    "expected_answer": "GIL prevents multiple native threads from executing Python bytecode simultaneously...",
    "retrieval_issue": "Missing chunk — конспект по async упоминает GIL лишь косвенно, основной ответ в другом документе."
  },
  {
    "scenario": "compare",
    "question": "Какие противоречия между документами?",
    "expected_answer": "Doc A: Python uses dynamic typing. Doc B: Python has optional static typing. Doc C: Python is purely interpreted (JIT exists)...",
    "retrieval_issue": "Wrong chunk priority — similarity search picks less relevant chunks first."
  }
]
```

---

## Verification

### Backend Tests (`test_documents.py`)

1. `test_ingest_text_document` — upload plain text, verify chunks created and source returned
2. `test_ingest_markdown_document` — upload markdown, verify header-aware chunking
3. `test_ingest_pdf_document` — upload small PDF, verify text extraction and chunking
4. `test_query_returns_answer_and_citations` — ingest doc, query, verify answer + citations
5. `test_query_empty_sources` — query with no documents ingested → 400 error
6. `test_delete_source` — delete source, verify chunks removed from ChromaDB
7. `test_list_sources` — ingest multiple docs, verify list
8. `test_demo_scenario_load` — load demo scenario, verify sources returned
9. `test_demo_scenario_unknown` — unknown scenario → 404
10. `test_failure_case_returned` — query demo question, verify FailureCaseOut in response

### Frontend Tests

- Verify DemoScenarios cards render and load
- Verify AnswerCard shows citations as clickable badges
- Verify FailureCasesPanel renders table rows
- Verify DocumentUploader accepts .md, .txt, .pdf files
- Verify SourcesList shows/deletes sources
- Verify empty state when no sources loaded

### Manual Verification

1. Load "Спроси по конспектам" demo → query "Что такое GIL?" → answer with citations + failure case
2. Load "Сравни 3 документа" → query about contradictions → response with cited contradictions
3. Upload custom .md file → query → answer with citations → no failure case panel
4. Delete source → verify it disappears and queries fail meaningfully

---

## Files Changed / Created

### New Files
- `backend/app/routes/documents.py`
- `backend/app/services/embedding_service.py`
- `backend/app/services/document_service.py`
- `backend/app/services/chroma_client.py`
- `backend/app/data/demo/` (вся папка с документами и failures.json)
- `backend/tests/test_documents.py`
- `frontend/app/document-qa/page.tsx`
- `frontend/app/document-qa/actions.ts`
- `frontend/components/document-qa/DemoScenarios.tsx`
- `frontend/components/document-qa/DocumentUploader.tsx`
- `frontend/components/document-qa/SourcesList.tsx`
- `frontend/components/document-qa/QuestionInput.tsx`
- `frontend/components/document-qa/AnswerCard.tsx`
- `frontend/components/document-qa/CitationBadge.tsx`
- `frontend/components/document-qa/FailureCasesPanel.tsx`

### Modified Files
- `backend/app/main.py` — register documents router
- `backend/app/schemas.py` — add new models
- `backend/requirements.txt` — add chromadb, tiktoken, PyPDF2
- `frontend/app/layout.tsx` — add Document QA link to nav
- `frontend/app/globals.css` — any new CSS custom properties if needed
- `frontend/types/ai.ts` — add document-related status types

### Not Changed
- `backend/app/services/llm_service.py` — existing LLM calls reused for answer generation
- `frontend/components/ai/ErrorState.tsx` — reused as-is
- `frontend/components/ai/JsonPreview.tsx` — reused for raw citation data
