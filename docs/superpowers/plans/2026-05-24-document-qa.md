# Document QA / RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Document QA module with file upload, chunking, vector search via ChromaDB, LLM-powered Q&A with citations, and failure case tracking for demo scenarios.

**Architecture:** New backend services (ChromaDB client, embedding, document ingestion/query) exposed via `/documents/*` endpoints. New frontend page with two tabs: demo scenarios and user document upload. Following existing patterns: FastAPI routes → service layer, Next.js server actions → client components.

**Tech Stack:** Python/FastAPI, ChromaDB, OpenAI embeddings (`text-embedding-3-small`), tiktoken, PyPDF2, Next.js 16, React 19, Tailwind v4, shadcn/ui.

---

## File Map

| File | Responsibility |
|------|----------------|
| `backend/app/schemas.py` | Add SourceCreate, SourceOut, QuestionRequest, QuestionResponse, CitationOut, FailureCaseOut |
| `backend/app/services/chroma_client.py` | Singleton wrapper: collection init, add, query, delete |
| `backend/app/services/embedding_service.py` | OpenAI embeddings API calls, `embed(texts: list[str]) -> list[list[float]]` |
| `backend/app/services/document_service.py` | Chunking (tiktoken), ingest, retrieval + LLM answer, failure case matching |
| `backend/app/routes/documents.py` | 5 endpoints: ingest, query, sources list, delete source, demo load |
| `backend/app/data/demo/` | 10 demo .md files + failures.json |
| `backend/tests/test_documents.py` | 10 tests using Fake services |
| `frontend/types/ai.ts` | Add `DocumentQAStatus` type |
| `frontend/app/document-qa/actions.ts` | 5 server actions: upload, query, getSources, deleteSource, loadDemo |
| `frontend/components/document-qa/DemoScenarios.tsx` | 4 scenario cards with Load button + predefined questions |
| `frontend/components/document-qa/DocumentUploader.tsx` | File input (.md/.txt/.pdf) + text paste textarea |
| `frontend/components/document-qa/SourcesList.tsx` | Loaded docs list with chunk count + delete |
| `frontend/components/document-qa/QuestionInput.tsx` | Text input + submit button |
| `frontend/components/document-qa/AnswerCard.tsx` | Answer text + inline CitationBadge[] |
| `frontend/components/document-qa/CitationBadge.tsx` | Clickable badge showing source + chunk |
| `frontend/components/document-qa/FailureCasesPanel.tsx` | Table: question, expected, actual, retrieval_issue |
| `frontend/app/document-qa/page.tsx` | Main page: two tabs, orchestrates all components |

---

### Task 1: Add schemas and dependencies

**Files:**
- Modify: `backend/app/schemas.py` — append new models
- Modify: `backend/requirements.txt` — append new dependencies

- [ ] **Step 1: Add new Pydantic models to schemas.py**

Open `backend/app/schemas.py` and append after the existing `HealthResponse` model:

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
    source_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class CitationOut(BaseModel):
    source_id: str
    source_filename: str
    chunk_position: int
    chunk_text: str


class FailureCaseOut(BaseModel):
    question: str
    expected_answer: str
    actual_answer: str
    retrieval_issue: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationOut]
    latency_ms: int
    failure_case: FailureCaseOut | None = None
```

Make sure `datetime` import is not duplicated — check if it's already imported in `schemas.py`. If not, add it.

- [ ] **Step 2: Add dependencies to requirements.txt**

Open `backend/requirements.txt` and append:

```
chromadb>=0.5.0
tiktoken>=0.7.0
PyPDF2>=3.0.0
```

- [ ] **Step 3: Install dependencies**

Run: `cd backend && pip install chromadb tiktoken PyPDF2`
Expected: packages install successfully.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas.py backend/requirements.txt
git commit -m "feat: add Document QA schemas and dependencies"
```

---

### Task 2: ChromaDB client wrapper

**Files:**
- Create: `backend/app/services/chroma_client.py`

- [ ] **Step 1: Create chroma_client.py**

```python
import os
import uuid
from typing import Any

import chromadb
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions

from app.config import get_settings


_COLLECTION_NAME = "documents"
_CLIENT: ClientAPI | None = None


def _get_chroma_client() -> ClientAPI:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    settings = get_settings()
    persist_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "chroma"
    )
    os.makedirs(persist_dir, exist_ok=True)

    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        api_base=settings.openai_base_url,
        model_name="text-embedding-3-small",
    )

    _CLIENT = chromadb.PersistentClient(path=persist_dir)
    _CLIENT.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return _CLIENT


def _collection():
    return _get_chroma_client().get_collection(_COLLECTION_NAME)


def add_chunks(chunks: list[dict[str, Any]]) -> list[str]:
    if not chunks:
        return []
    chunk_ids = [str(uuid.uuid4()) for _ in chunks]
    _collection().add(
        ids=chunk_ids,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source_id": c["source_id"],
                "filename": c["filename"],
                "chunk_position": c["chunk_position"],
            }
            for c in chunks
        ],
    )
    return chunk_ids


def query_chunks(
    query_text: str,
    source_ids: list[str] | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    where_filter = None
    if source_ids:
        where_filter = {"source_id": {"$in": source_ids}}

    results = _collection().query(
        query_texts=[query_text],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    out: list[dict[str, Any]] = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            out.append({
                "id": chunk_id,
                "text": results["documents"][0][i] if results["documents"] else "",
                "source_id": results["metadatas"][0][i]["source_id"] if results["metadatas"] else "",
                "filename": results["metadatas"][0][i]["filename"] if results["metadatas"] else "",
                "chunk_position": results["metadatas"][0][i]["chunk_position"] if results["metadatas"] else 0,
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })
    return out


def delete_source_chunks(source_id: str) -> None:
    col = _collection()
    results = col.get(where={"source_id": source_id})
    if results["ids"]:
        col.delete(ids=results["ids"])


def reset_for_tests() -> None:
    global _CLIENT
    client = _get_chroma_client()
    try:
        client.delete_collection(_COLLECTION_NAME)
    except Exception:
        pass
    _CLIENT = None
```

- [ ] **Step 2: Verify ChromaDB import works**

Run: `cd backend && python -c "import chromadb; print(chromadb.__version__)"`
Expected: prints version, no errors.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/chroma_client.py
git commit -m "feat: add ChromaDB client wrapper"
```

---

### Task 3: Embedding service

**Files:**
- Create: `backend/app/services/embedding_service.py`

- [ ] **Step 1: Create embedding_service.py**

```python
from openai import AsyncOpenAI

from app.config import get_settings


_embedding_model = "text-embedding-3-small"


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    settings = get_settings()
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    response = await client.embeddings.create(
        model=_embedding_model,
        input=texts,
    )
    return [d.embedding for d in response.data]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/embedding_service.py
git commit -m "feat: add embedding service"
```

---

### Task 4: Document service (chunking, ingest, query)

**Files:**
- Create: `backend/app/services/document_service.py`

- [ ] **Step 1: Create document_service.py**

```python
import io
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tiktoken
from PyPDF2 import PdfReader

from app.config import get_settings
from app.core.errors import AppError
from app.schemas import (
    CitationOut,
    FailureCaseOut,
    QuestionRequest,
    QuestionResponse,
    SourceCreate,
    SourceOut,
)
from app.services.chroma_client import add_chunks, delete_source_chunks, query_chunks
from app.services.llm_service import LLMService


_TOKENIZER = tiktoken.get_encoding("cl100k_base")
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 100
_DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def _count_tokens(text: str) -> int:
    return len(_TOKENIZER.encode(text))


def _chunk_text(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _count_tokens(para)
        if current_tokens + para_tokens > _CHUNK_SIZE and current:
            chunks.append("\n\n".join(current))
            overlap_point = max(0, len(current) - 1)
            current = current[overlap_point:]
            current_tokens = sum(_count_tokens(p) for p in current)
        current.append(para)
        current_tokens += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    if not chunks:
        chunks = [text]
    return chunks


def _chunk_markdown(text: str) -> list[str]:
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    all_chunks: list[str] = []
    for section in sections:
        if not section.strip():
            continue
        all_chunks.extend(_chunk_text(section))
    if not all_chunks:
        all_chunks = _chunk_text(text)
    return all_chunks


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


# In-memory source registry (maps source_id -> metadata)
_sources: dict[str, dict[str, Any]] = {}


class DocumentService:
    def __init__(self) -> None:
        self._llm_service: LLMService | None = None

    def _get_llm(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service

    async def ingest(self, payload: SourceCreate) -> SourceOut:
        source_id = str(uuid.uuid4())
        content = payload.content

        if payload.content_type == "application/pdf":
            try:
                content = _extract_pdf_text(content.encode("latin-1"))
            except Exception:
                pass

        if payload.content_type == "text/markdown":
            chunks = _chunk_markdown(content)
        else:
            chunks = _chunk_text(content)

        chunk_records = [
            {
                "source_id": source_id,
                "filename": payload.filename,
                "chunk_position": i,
                "text": chunk,
            }
            for i, chunk in enumerate(chunks)
        ]

        add_chunks(chunk_records)

        now = datetime.now(timezone.utc)
        _sources[source_id] = {
            "id": source_id,
            "filename": payload.filename,
            "content_type": payload.content_type,
            "chunk_count": len(chunks),
            "created_at": now,
        }

        return SourceOut(
            id=source_id,
            filename=payload.filename,
            content_type=payload.content_type,
            chunk_count=len(chunks),
            created_at=now,
        )

    async def query(self, payload: QuestionRequest) -> QuestionResponse:
        if not _sources:
            raise AppError(
                "NO_DOCUMENTS",
                "No documents have been ingested. Upload or load a demo scenario first.",
                400,
            )

        started = time.perf_counter()
        results = query_chunks(
            query_text=payload.question,
            source_ids=payload.source_ids,
            top_k=payload.top_k,
        )

        context_parts: list[str] = []
        for r in results:
            context_parts.append(
                f"[Source: {r['filename']}, Chunk {r['chunk_position']}]\n{r['text']}"
            )
        context = "\n\n".join(context_parts)

        settings = get_settings()
        prompt = (
            "You are a helpful assistant answering questions based on the provided "
            "document chunks. Answer the question using ONLY the context below.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {payload.question}\n\n"
            "Answer concisely. Cite sources by mentioning the filename and chunk number "
            "when you use information from a specific chunk."
        )

        client = self._get_llm()._get_client()
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        answer = response.choices[0].message.content or ""

        citations = [
            CitationOut(
                source_id=r["source_id"],
                source_filename=r["filename"],
                chunk_position=r["chunk_position"],
                chunk_text=r["text"][:500],
            )
            for r in results
        ]

        latency_ms = int((time.perf_counter() - started) * 1000)

        failure_case = _match_failure_case(payload.question, answer)

        return QuestionResponse(
            question=payload.question,
            answer=answer,
            citations=citations,
            latency_ms=latency_ms,
            failure_case=failure_case,
        )

    def list_sources(self) -> list[SourceOut]:
        return [
            SourceOut(
                id=s["id"],
                filename=s["filename"],
                content_type=s["content_type"],
                chunk_count=s["chunk_count"],
                created_at=s["created_at"],
            )
            for s in _sources.values()
        ]

    def delete_source(self, source_id: str) -> None:
        if source_id not in _sources:
            raise AppError(
                "SOURCE_NOT_FOUND",
                f"Source '{source_id}' not found.",
                404,
            )
        delete_source_chunks(source_id)
        del _sources[source_id]

    async def load_demo_scenario(self, scenario: str) -> list[SourceOut]:
        scenario_dir = _DEMO_DIR / scenario
        if not scenario_dir.exists() or not scenario_dir.is_dir():
            raise AppError(
                "SCENARIO_NOT_FOUND",
                f"Demo scenario '{scenario}' not found. Available: {', '.join(_list_scenarios())}",
                404,
            )

        sources: list[SourceOut] = []
        for file_path in sorted(scenario_dir.iterdir()):
            if not file_path.is_file() or file_path.suffix != ".md":
                continue
            content = file_path.read_text(encoding="utf-8")
            source = await self.ingest(
                SourceCreate(
                    filename=file_path.name,
                    content_type="text/markdown",
                    content=content,
                )
            )
            sources.append(source)
        return sources


_FAILURES: list[dict[str, Any]] | None = None


def _load_failures() -> list[dict[str, Any]]:
    global _FAILURES
    if _FAILURES is None:
        path = _DEMO_DIR / "failures.json"
        if path.exists():
            _FAILURES = json.loads(path.read_text(encoding="utf-8"))
        else:
            _FAILURES = []
    return _FAILURES


def _match_failure_case(question: str, actual_answer: str) -> FailureCaseOut | None:
    for f in _load_failures():
        if f["question"].strip().lower() == question.strip().lower():
            return FailureCaseOut(
                question=f["question"],
                expected_answer=f["expected_answer"],
                actual_answer=actual_answer,
                retrieval_issue=f["retrieval_issue"],
            )
    return None


def _list_scenarios() -> list[str]:
    if not _DEMO_DIR.exists():
        return []
    return [
        d.name
        for d in _DEMO_DIR.iterdir()
        if d.is_dir() and any(f.suffix == ".md" for f in d.iterdir())
    ]


def reset_for_tests() -> None:
    global _sources
    _sources.clear()
    clear_failure_cache()


def clear_failure_cache() -> None:
    global _FAILURES
    _FAILURES = None
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/document_service.py
git commit -m "feat: add document service with chunking, ingest, query"
```

---

### Task 5: Demo data

**Files:**
- Create: `backend/app/data/demo/conspectus/python-basics.md`
- Create: `backend/app/data/demo/conspectus/python-oop.md`
- Create: `backend/app/data/demo/conspectus/python-async.md`
- Create: `backend/app/data/demo/project-docs/roadmap.md`
- Create: `backend/app/data/demo/project-docs/architecture.md`
- Create: `backend/app/data/demo/compare/doc-a.md`
- Create: `backend/app/data/demo/compare/doc-b.md`
- Create: `backend/app/data/demo/compare/doc-c.md`
- Create: `backend/app/data/demo/faq/notes-1.md`
- Create: `backend/app/data/demo/faq/notes-2.md`
- Create: `backend/app/data/demo/failures.json`
- Create: `backend/.gitignore` — add chroma/ directory

- [ ] **Step 1: Create conspectus/python-basics.md**

```markdown
# Python Basics

## Variables and Types

Python is dynamically typed. You don't need to declare types. Variables are created when you assign a value to them.

```python
name = "Alice"
age = 30
height = 5.8
is_student = False
```

Python supports int, float, str, bool, list, tuple, dict, set types.

## Control Flow

Python uses indentation for code blocks. If statements, for loops, while loops — all use colons and indentation.

```python
if age >= 18:
    print("Adult")
elif age >= 13:
    print("Teenager")
else:
    print("Child")
```

## Functions

Functions are defined with `def`. They can have default arguments, keyword arguments, and variable-length arguments.

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"
```

## The GIL

The Global Interpreter Lock (GIL) is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecode at once. This means CPU-bound Python programs won't benefit from multi-threading.
```

- [ ] **Step 2: Create conspectus/python-oop.md**

```markdown
# Python OOP

## Classes

Python classes are defined with `class` keyword. The `__init__` method is the constructor.

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
```

## Inheritance

Python supports single and multiple inheritance. Use `super()` to call parent methods.

```python
class Student(Person):
    def __init__(self, name, age, student_id):
        super().__init__(name, age)
        self.student_id = student_id
```

## Dunder Methods

Special methods with double underscores: `__str__`, `__repr__`, `__eq__`, `__lt__`, `__len__`, `__getitem__`. These enable operator overloading and integration with Python built-ins.

## Type Hints and Static Typing

Python 3.5+ supports optional type hints. While Python remains dynamically typed at runtime, type checkers like mypy and pyright can catch type errors before execution. Python also supports TypeVar for generics, Protocol for structural subtyping, and TypedDict for typed dictionaries.
```

- [ ] **Step 3: Create conspectus/python-async.md**

```markdown
# Python Async Programming

## async/await

Python's `asyncio` library provides infrastructure for writing concurrent code using the `async`/`await` syntax.

```python
import asyncio

async def fetch_data(url):
    # Simulate network request
    await asyncio.sleep(1)
    return f"Data from {url}"
```

## Event Loop

The event loop is the core of asyncio. It runs async tasks, handles I/O events, and schedules callbacks. Use `asyncio.run()` to start the event loop.

## GIL and Async

The GIL doesn't prevent asyncio from being useful for I/O-bound tasks. Async code yields control at `await` points, allowing other coroutines to run. For CPU-bound work, use `run_in_executor` or multiprocessing instead.

## Coroutines vs Threads

Coroutines are lighter than threads. Thousands of coroutines can run concurrently in a single thread. Threads are better for CPU-bound work (if GIL allows) or when calling blocking C extensions.
```

- [ ] **Step 4: Create project-docs/roadmap.md**

```markdown
# AI Primitives Playground — Roadmap

## Completed Modules

1. **Brief Parser** — Structured text analysis: input text → /analyze endpoint → topics, pain_points, risks, next_questions.
2. **AI Form Assistant** — Project form auto-fill: describe project → /form-assistant → suggested form values with user approval.
3. **Tool Calling Playground** — LLM decides which tool to call → user approves side-effect tools → tool executed.

## Architecture

- Backend: FastAPI on port 8000, Pydantic v2 schemas, service-layer pattern
- Frontend: Next.js 16, React 19, Tailwind v4, shadcn/ui
- AI: OpenAI-compatible API for LLM calls
- Testing: pytest for backend, Vitest for frontend

## Key Design Decisions

- AI logic stays in backend service layer, never in frontend routes
- Tool execution with safety approval: side-effect tools require `approved: true`
- All responses validated with Pydantic schemas
- Request logging middleware on every endpoint
```

- [ ] **Step 5: Create project-docs/architecture.md**

```markdown
# AI Primitives Architecture

## Backend Structure

The backend follows a layered architecture:
- `routes/` — HTTP handlers, thin controllers
- `services/` — Business logic, LLM calls, tool execution
- `core/` — Error classes, middleware
- `schemas.py` — Pydantic models for request/response validation

## Frontend Structure

The frontend uses Next.js App Router:
- `app/<module>/page.tsx` — Client components with state management
- `app/<module>/actions.ts` — Server actions wrapping backend API calls
- `components/ai/` — Reusable AI UI components (ApprovalCard, ErrorState, etc.)
- `components/ui/` — shadcn/ui primitives

## API Flow

Frontend server action → fetch() to FastAPI backend → Pydantic validation → service layer → OpenAI API → response → Zod validation on frontend.
```

- [ ] **Step 6: Create compare/doc-a.md**

```markdown
# Python Language Overview A

Python is a high-level, interpreted programming language known for its readability.

## Type System

Python uses dynamic typing exclusively. Variables can hold any type, and type checking happens at runtime. There is no compile-time type safety. This makes Python flexible but can lead to runtime errors that statically typed languages catch earlier.

## Execution Model

Python code is executed line by line by the Python interpreter. There is no compilation step. Python programs run as plain text files that are parsed and executed at runtime. This makes Python an interpreted language through and through.
```

- [ ] **Step 7: Create compare/doc-b.md**

```markdown
# Python Language Overview B

Python is a multi-paradigm language that supports object-oriented, procedural, and functional programming styles.

## Type System

Python has an optional static type system through type hints. The `typing` module provides TypeVar, Generic, Protocol, and TypedDict that enable full static type checking with tools like mypy. Large codebases like Django and SQLAlchemy ship with type stubs. Python's type system continues to evolve with each release.

## Execution Model

Python compiles source code to bytecode before executing it on the Python Virtual Machine. The `.pyc` files you see in `__pycache__` directories are compiled bytecode. For performance, PyPy uses JIT compilation for frequently executed code paths, achieving near-C speeds for some workloads.
```

- [ ] **Step 8: Create compare/doc-c.md**

```markdown
# Python Language Overview C

Python is one of the most popular programming languages, widely used in data science, web development, and automation.

## Type System

Python has always been dynamically typed — that's one of its core features. Variables don't have types, objects do. This is fundamental to Python's design philosophy and won't change. Attempts to add static typing are add-ons, not part of the language itself.

## Execution Model

Python is purely interpreted. Unlike Java or C++, there's no compiler step in the development workflow. You write code, you run it. The interpreter reads and executes each line sequentially. This is why Python is great for scripting and rapid prototyping — zero compile time, instant feedback.
```

- [ ] **Step 9: Create faq/notes-1.md**

```markdown
# FastAPI FAQ Notes

## Q: What is FastAPI?

FastAPI is a modern Python web framework for building APIs. It's built on Starlette and Pydantic, and it's one of the fastest Python frameworks available.

## Q: How do you define a route?

You use decorators like `@app.get("/path")` or `@app.post("/path")`. Each route takes a function that returns a response.

## Q: How does validation work?

FastAPI uses Pydantic models. When you declare a parameter with a Pydantic type, FastAPI automatically validates the request body against that model and returns detailed errors if validation fails.

## Q: How do you handle async?

FastAPI supports `async def` natively. Async endpoints run in an event loop, letting you use `await` for database queries, HTTP calls, and other I/O operations.

## Q: What is dependency injection in FastAPI?

FastAPI's `Depends()` function lets you declare dependencies that FastAPI resolves automatically. Dependencies can be functions, classes, or async callables. This is used for auth, database sessions, and configuration.
```

- [ ] **Step 10: Create faq/notes-2.md**

```markdown
# Next.js FAQ Notes

## Q: What is Next.js App Router?

The App Router is Next.js's modern routing system based on the file system. Pages are `page.tsx`, layouts are `layout.tsx`, and API routes are `route.ts`.

## Q: What are Server Components?

Server Components run on the server and never ship client-side JavaScript. They can directly access databases and filesystems. They are the default in App Router.

## Q: What are Server Actions?

Server Actions are async functions marked with `"use server"` that run on the server. They can be called from Client Components and handle form submissions, data mutations, and API calls without creating a separate API route.

## Q: How do you handle loading states?

Next.js provides `loading.tsx` files for route-level loading UI, and React's `useTransition` hook for pending states during server action calls.

## Q: What is static vs dynamic rendering?

By default, Next.js tries to statically render pages at build time. When you use dynamic functions like `cookies()`, `headers()`, or `searchParams`, the page becomes dynamically rendered at request time.
```

- [ ] **Step 11: Create failures.json**

```json
[
  {
    "scenario": "conspectus",
    "question": "Как работает GIL в Python?",
    "expected_answer": "GIL (Global Interpreter Lock) — это мьютекс, который защищает доступ к объектам Python. Он предотвращает одновременное выполнение байткода Python несколькими потоками. Из-за GIL CPU-bound программы не получают выигрыша от многопоточности. При этом GIL не мешает asyncio для I/O-bound задач — корутины могут переключаться на await.",
    "retrieval_issue": "Missing chunk — конспект python-basics.md содержит основное определение GIL, но только один абзац. Конспект python-async.md упоминает GIL лишь косвенно (про asyncio). Retrieval вернул чанки из async-конспекта вместо основного определения."
  },
  {
    "scenario": "compare",
    "question": "Какие противоречия между документами?",
    "expected_answer": "1) Type system: Doc A утверждает что Python использует только динамическую типизацию, но Doc B описывает опциональную статическую типизацию через TypeVar и type hints. Doc C отрицает статическую типизацию. 2) Execution model: Doc A и Doc C говорят что Python чисто интерпретируемый, но Doc B описывает компиляцию в байткод и JIT в PyPy.",
    "retrieval_issue": "Wrong chunk priority — similarity search возвращает чанки с общим описанием Python вместо чанков где напрямую описаны противоречия. Самые релевантные для сравнения чанки имеют более низкий similarity score."
  },
  {
    "scenario": "faq",
    "question": "Сравни FastAPI и Next.js по маршрутизации и валидации",
    "expected_answer": "FastAPI использует декораторы (@app.get) и Pydantic для валидации. Next.js App Router использует файловую систему (page.tsx, route.ts) и Zod для валидации. FastAPI валидация встроена в параметры, Next.js требует ручного вызова parse().",
    "retrieval_issue": "Missing chunk — retrieval вернул только чанки про FastAPI, чанки про Next.js маршрутизацию не попали в top-k. Возможно из-за того что вопрос упоминает FastAPI первым."
  }
]
```

- [ ] **Step 12: Add chroma/ to .gitignore**

Check if `backend/.gitignore` exists. If not, create it; if yes, append `data/chroma/`:

```
data/chroma/
```

- [ ] **Step 13: Commit**

```bash
git add backend/app/data/demo/ backend/.gitignore
git commit -m "feat: add demo documents and failure cases for Document QA"
```

---

### Task 6: Documents route

**Files:**
- Create: `backend/app/routes/documents.py`

- [ ] **Step 1: Create documents.py**

```python
from fastapi import APIRouter, Request

from app.schemas import QuestionRequest, QuestionResponse, SourceCreate, SourceOut
from app.services.document_service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(request: Request) -> DocumentService:
    service = getattr(request.app.state, "document_service", None)
    if service is None:
        service = DocumentService()
        request.app.state.document_service = service
    return service


@router.post(
    "/ingest",
    response_model=SourceOut,
    summary="Ingest a document",
    description="Upload and chunk a document for Q&A.",
)
async def ingest_document(
    payload: SourceCreate,
    request: Request,
) -> SourceOut:
    service = get_document_service(request)
    return await service.ingest(payload)


@router.post(
    "/query",
    response_model=QuestionResponse,
    summary="Query documents",
    description="Ask a question and get an answer with citations from ingested documents.",
)
async def query_documents(
    payload: QuestionRequest,
    request: Request,
) -> QuestionResponse:
    service = get_document_service(request)
    return await service.query(payload)


@router.get(
    "/sources",
    response_model=list[SourceOut],
    summary="List sources",
    description="List all ingested document sources.",
)
async def list_sources(request: Request) -> list[SourceOut]:
    service = get_document_service(request)
    return service.list_sources()


@router.delete(
    "/sources/{source_id}",
    summary="Delete a source",
    description="Delete a document source and all its chunks.",
)
async def delete_source(source_id: str, request: Request) -> dict:
    service = get_document_service(request)
    service.delete_source(source_id)
    return {"deleted": True}


@router.post(
    "/demo/{scenario}",
    response_model=list[SourceOut],
    summary="Load demo scenario",
    description="Load a pre-built demo scenario with documents.",
)
async def load_demo_scenario(
    scenario: str,
    request: Request,
) -> list[SourceOut]:
    service = get_document_service(request)
    return await service.load_demo_scenario(scenario)
```

- [ ] **Step 2: Register route in main.py**

Open `backend/app/main.py`. Change the imports and router registration:

```python
from app.routes import analyze, chat, documents, form_assistant, health, tools
```

Add after `app.include_router(tools.router)`:

```python
app.include_router(documents.router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/documents.py backend/app/main.py
git commit -m "feat: add documents route with ingest/query/sources/demo endpoints"
```

---

### Task 7: Backend tests

**Files:**
- Create: `backend/tests/test_documents.py`

- [ ] **Step 1: Create test_documents.py**

```python
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import QuestionResponse, CitationOut, FailureCaseOut, SourceOut
from app.services.chroma_client import reset_for_tests as reset_chroma
from app.services.document_service import reset_for_tests as reset_docs


client = TestClient(app)


FAKE_SOURCE_ID = "test-source-uuid-123"


def teardown_function():
    if hasattr(app.state, "document_service"):
        del app.state.document_service
    reset_docs()
    reset_chroma()


# --- Ingest Tests ---

@patch("app.services.document_service.add_chunks")
def test_ingest_plain_text(mock_add):
    mock_add.return_value = ["chunk-1", "chunk-2"]
    payload = {
        "filename": "test.txt",
        "content_type": "text/plain",
        "content": "This is paragraph one.\n\nThis is paragraph two.",
    }
    response = client.post("/documents/ingest", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "test.txt"
    assert body["content_type"] == "text/plain"
    assert body["chunk_count"] >= 1
    assert body["id"] is not None
    assert body["created_at"] is not None


@patch("app.services.document_service.add_chunks")
def test_ingest_markdown(mock_add):
    mock_add.return_value = ["c1", "c2", "c3"]
    payload = {
        "filename": "readme.md",
        "content_type": "text/markdown",
        "content": "## Section One\nContent here.\n\n## Section Two\nMore content.",
    }
    response = client.post("/documents/ingest", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "readme.md"


def test_ingest_empty_content():
    response = client.post(
        "/documents/ingest",
        json={"filename": "x.txt", "content_type": "text/plain", "content": ""},
    )
    assert response.status_code == 422


# --- Query Tests ---

@patch("app.services.document_service.add_chunks")
@patch("app.services.document_service.query_chunks")
@patch.object(
    __import__("app.services.document_service", fromlist=["LLMService"]),
    "LLMService",
)
def test_query_returns_answer_and_citations(MockLLM, mock_query, mock_add):
    mock_add.return_value = ["c1", "c2"]
    mock_query.return_value = [
        {
            "id": "c1",
            "text": "FastAPI is fast.",
            "source_id": FAKE_SOURCE_ID,
            "filename": "test.txt",
            "chunk_position": 0,
            "distance": 0.1,
        }
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value.choices = [
        type("Choice", (), {"message": type("Msg", (), {"content": "FastAPI is fast."})})()
    ]
    MockLLM.return_value._get_client.return_value = mock_client

    # Ingest first
    client.post(
        "/documents/ingest",
        json={"filename": "test.txt", "content_type": "text/plain", "content": "FastAPI is a modern web framework.\n\nIt is very fast."},
    )

    response = client.post(
        "/documents/query",
        json={"question": "What is FastAPI?", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "FastAPI is fast."
    assert len(body["citations"]) == 1
    assert body["citations"][0]["source_filename"] == "test.txt"


def test_query_empty_sources():
    reset_docs()
    response = client.post(
        "/documents/query",
        json={"question": "What is FastAPI?"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "NO_DOCUMENTS"


# --- Sources Tests ---

@patch("app.services.document_service.add_chunks")
def test_list_sources(mock_add):
    mock_add.return_value = ["c1"]
    client.post(
        "/documents/ingest",
        json={"filename": "a.txt", "content_type": "text/plain", "content": "Hello world."},
    )
    client.post(
        "/documents/ingest",
        json={"filename": "b.txt", "content_type": "text/plain", "content": "Another doc."},
    )

    response = client.get("/documents/sources")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {s["filename"] for s in body} == {"a.txt", "b.txt"}


@patch("app.services.document_service.add_chunks")
@patch("app.services.document_service.delete_source_chunks")
def test_delete_source(mock_delete, mock_add):
    mock_add.return_value = ["c1"]
    resp = client.post(
        "/documents/ingest",
        json={"filename": "x.txt", "content_type": "text/plain", "content": "Hello."},
    )
    source_id = resp.json()["id"]

    del_resp = client.delete(f"/documents/sources/{source_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    list_resp = client.get("/documents/sources")
    assert len(list_resp.json()) == 0


def test_delete_nonexistent_source():
    response = client.delete("/documents/sources/nonexistent")
    assert response.status_code == 404


# --- Demo Tests ---

def test_demo_scenario_unknown():
    response = client.post("/documents/demo/nonexistent")
    assert response.status_code == 404


@patch("app.services.document_service.add_chunks")
def test_demo_scenario_load(mock_add):
    mock_add.return_value = ["c1", "c2", "c3"]
    response = client.post("/documents/demo/compare")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert all(s["content_type"] == "text/markdown" for s in body)
```

- [ ] **Step 2: Run tests**

Run: `cd backend && python -m pytest tests/test_documents.py -v`
Expected: all 8 tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_documents.py
git commit -m "test: add Document QA backend tests"
```

---

### Task 8: Frontend types

**Files:**
- Modify: `frontend/types/ai.ts`

- [ ] **Step 1: Add DocumentQAStatus type**

Open `frontend/types/ai.ts` and append:

```typescript
export type DocumentQAStatus =
  | "idle"
  | "loading"
  | "success"
  | "error";
```

- [ ] **Step 2: Commit**

```bash
git add frontend/types/ai.ts
git commit -m "feat: add DocumentQAStatus type"
```

---

### Task 9: Frontend server actions

**Files:**
- Create: `frontend/app/document-qa/actions.ts`

- [ ] **Step 1: Create actions.ts**

```typescript
"use server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

function extractErrorMessage(data: unknown, status: number): string {
  if (data && typeof data === "object" && "error" in data) {
    const err = (data as { error?: { code?: string; message?: string } }).error;
    if (err?.message) {
      const prefix = err.code ? `[${err.code}] ` : "";
      return `${prefix}${err.message}`;
    }
  }
  return `Request failed with status ${status}`;
}

export interface SourceOut {
  id: string;
  filename: string;
  content_type: string;
  chunk_count: number;
  created_at: string;
}

export interface CitationOut {
  source_id: string;
  source_filename: string;
  chunk_position: number;
  chunk_text: string;
}

export interface FailureCaseOut {
  question: string;
  expected_answer: string;
  actual_answer: string;
  retrieval_issue: string;
}

export interface QuestionResponse {
  question: string;
  answer: string;
  citations: CitationOut[];
  latency_ms: number;
  failure_case: FailureCaseOut | null;
}

export async function uploadDocument(
  filename: string,
  content: string,
  contentType: string = "text/plain",
): Promise<SourceOut> {
  const res = await fetch(`${BACKEND_URL}/documents/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      filename,
      content_type: contentType,
      content,
    }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}

export async function queryDocument(
  question: string,
  topK: number = 5,
): Promise<QuestionResponse> {
  const res = await fetch(`${BACKEND_URL}/documents/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}

export async function getSources(): Promise<SourceOut[]> {
  const res = await fetch(`${BACKEND_URL}/documents/sources`);

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}

export async function deleteSource(sourceId: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/documents/sources/${sourceId}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }
}

export async function loadDemoScenario(
  scenario: string,
): Promise<SourceOut[]> {
  const res = await fetch(`${BACKEND_URL}/documents/demo/${scenario}`, {
    method: "POST",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(extractErrorMessage(data, res.status));
  }

  return res.json();
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/document-qa/actions.ts
git commit -m "feat: add Document QA server actions"
```

---

### Task 10: Frontend components

**Files:**
- Create: `frontend/components/document-qa/DemoScenarios.tsx`
- Create: `frontend/components/document-qa/DocumentUploader.tsx`
- Create: `frontend/components/document-qa/SourcesList.tsx`
- Create: `frontend/components/document-qa/QuestionInput.tsx`
- Create: `frontend/components/document-qa/AnswerCard.tsx`
- Create: `frontend/components/document-qa/CitationBadge.tsx`
- Create: `frontend/components/document-qa/FailureCasesPanel.tsx`

- [ ] **Step 1: Create DemoScenarios.tsx**

```typescript
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, FolderGit2, GitCompare, MessagesSquare, Loader2 } from "lucide-react";

interface ScenarioDef {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  questions: string[];
}

const SCENARIOS: ScenarioDef[] = [
  {
    id: "conspectus",
    title: "Спроси по конспектам",
    description: "3 конспекта по Python: синтаксис, ООП, async. Задайте вопросы по материалу.",
    icon: <BookOpen className="h-5 w-5" />,
    questions: [
      "Как работает GIL в Python?",
      "Что такое dunder-методы?",
      "Зачем нужен event loop в asyncio?",
    ],
  },
  {
    id: "project-docs",
    title: "Спроси по документации проекта",
    description: "ROADMAP.md и описание архитектуры AI Primitives. Узнайте как устроен проект.",
    icon: <FolderGit2 className="h-5 w-5" />,
    questions: [
      "Какие модули уже реализованы?",
      "Как устроена архитектура бэкенда?",
    ],
  },
  {
    id: "compare",
    title: "Сравни 3 документа и найди противоречия",
    description: "Три документа о Python с намеренными расхождениями. Найдите, где они противоречат друг другу.",
    icon: <GitCompare className="h-5 w-5" />,
    questions: [
      "Какие противоречия между документами?",
    ],
  },
  {
    id: "faq",
    title: "Собери FAQ из набора заметок",
    description: "Заметки с вопросами-ответами по FastAPI и Next.js. Сгенерируйте сводный FAQ.",
    icon: <MessagesSquare className="h-5 w-5" />,
    questions: [
      "Сравни FastAPI и Next.js по маршрутизации и валидации",
      "Что такое FastAPI?",
    ],
  },
];

interface DemoScenariosProps {
  onLoad: (scenarioId: string) => void;
  onQuestionClick: (question: string) => void;
  loadedScenario: string | null;
  loading: boolean;
}

export function DemoScenarios({
  onLoad,
  onQuestionClick,
  loadedScenario,
  loading,
}: DemoScenariosProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {SCENARIOS.map((s) => {
        const isLoaded = loadedScenario === s.id;
        const isLoading = loading && loadedScenario === s.id;

        return (
          <Card key={s.id} className={isLoaded ? "border-blue-500/50" : ""}>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                {s.icon}
                <CardTitle className="text-base">{s.title}</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">{s.description}</p>
              {!isLoaded ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onLoad(s.id)}
                  disabled={loading}
                >
                  {isLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  {isLoading ? "Loading..." : "Load Scenario"}
                </Button>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase">
                    Questions
                  </p>
                  {s.questions.map((q) => (
                    <Button
                      key={q}
                      variant="ghost"
                      size="sm"
                      className="w-full justify-start text-left text-sm h-auto py-2"
                      onClick={() => onQuestionClick(q)}
                    >
                      {q}
                    </Button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Create DocumentUploader.tsx**

```typescript
"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Upload, FileText } from "lucide-react";

interface DocumentUploaderProps {
  onUpload: (filename: string, content: string, contentType: string) => Promise<void>;
  disabled: boolean;
}

export function DocumentUploader({ onUpload, disabled }: DocumentUploaderProps) {
  const [textContent, setTextContent] = useState("");
  const [textFilename, setTextFilename] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split(".").pop()?.toLowerCase();
    const typeMap: Record<string, string> = {
      md: "text/markdown",
      txt: "text/plain",
      pdf: "application/pdf",
    };
    const contentType = typeMap[ext ?? ""] ?? "text/plain";

    setUploading(true);
    try {
      const content = await file.text();
      await onUpload(file.name, content, contentType);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handlePasteUpload = async () => {
    if (!textContent.trim() || !textFilename.trim()) return;
    setUploading(true);
    try {
      await onUpload(textFilename, textContent, "text/plain");
      setTextContent("");
      setTextFilename("");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Upload File (.md, .txt, .pdf)</Label>
        <div className="flex items-center gap-2">
          <Input
            ref={fileInputRef}
            type="file"
            accept=".md,.txt,.pdf"
            onChange={handleFileUpload}
            disabled={disabled || uploading}
            className="flex-1"
          />
          {uploading && <Loader2 className="h-4 w-4 animate-spin" />}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Or paste text</Label>
        <Input
          placeholder="Document filename..."
          value={textFilename}
          onChange={(e) => setTextFilename(e.target.value)}
          disabled={disabled || uploading}
        />
        <Textarea
          placeholder="Paste document text here..."
          value={textContent}
          onChange={(e) => setTextContent(e.target.value)}
          rows={4}
          disabled={disabled || uploading}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={handlePasteUpload}
          disabled={!textContent.trim() || !textFilename.trim() || disabled || uploading}
        >
          {uploading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <FileText className="mr-2 h-4 w-4" />
          )}
          Add Document
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create SourcesList.tsx**

```typescript
"use client";

import { Button } from "@/components/ui/button";
import { Loader2, Trash2, FileText } from "lucide-react";
import type { SourceOut } from "@/app/document-qa/actions";

interface SourcesListProps {
  sources: SourceOut[];
  onDelete: (id: string) => void;
  deleting: string | null;
}

export function SourcesList({ sources, onDelete, deleting }: SourcesListProps) {
  if (sources.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium">Ingested Documents</h3>
      <div className="space-y-1">
        {sources.map((s) => (
          <div
            key={s.id}
            className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
          >
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span>{s.filename}</span>
              <span className="text-xs text-muted-foreground">
                ({s.chunk_count} chunks)
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onDelete(s.id)}
              disabled={deleting === s.id}
            >
              {deleting === s.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create QuestionInput.tsx**

```typescript
"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Send } from "lucide-react";

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  disabled: boolean;
  loading: boolean;
}

export function QuestionInput({ onSubmit, disabled, loading }: QuestionInputProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const input = form.elements.namedItem("question") as HTMLInputElement;
    if (input.value.trim()) {
      onSubmit(input.value.trim());
      input.value = "";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        name="question"
        placeholder={disabled ? "Upload documents to ask questions..." : "Ask a question about your documents..."}
        disabled={disabled || loading}
        className="flex-1"
      />
      <Button type="submit" disabled={disabled || loading}>
        {loading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Send className="mr-2 h-4 w-4" />
        )}
        {loading ? "Thinking..." : "Ask"}
      </Button>
    </form>
  );
}
```

- [ ] **Step 5: Create CitationBadge.tsx**

```typescript
"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";
import type { CitationOut } from "@/app/document-qa/actions";

interface CitationBadgeProps {
  citation: CitationOut;
}

export function CitationBadge({ citation }: CitationBadgeProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="inline-block">
      <Badge
        variant="secondary"
        className="cursor-pointer gap-1"
        onClick={() => setExpanded(!expanded)}
      >
        <FileText className="h-3 w-3" />
        {citation.source_filename} [chunk {citation.chunk_position}]
      </Badge>
      {expanded && (
        <div className="mt-1 rounded-md border bg-muted/50 p-2 text-xs text-muted-foreground max-w-md">
          {citation.chunk_text}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Create AnswerCard.tsx**

```typescript
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CitationBadge } from "./CitationBadge";
import { FailureCasesPanel } from "./FailureCasesPanel";
import type { QuestionResponse } from "@/app/document-qa/actions";

interface AnswerCardProps {
  response: QuestionResponse;
}

export function AnswerCard({ response }: AnswerCardProps) {
  return (
    <Card className="border-blue-500/30">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Answer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {response.answer}
        </p>

        {response.citations.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground uppercase">
              Sources
            </p>
            <div className="flex flex-wrap gap-1">
              {response.citations.map((c, i) => (
                <CitationBadge key={`${c.source_id}-${c.chunk_position}-${i}`} citation={c} />
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          {response.latency_ms}ms
        </p>

        {response.failure_case && (
          <FailureCasesPanel failureCase={response.failure_case} />
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 7: Create FailureCasesPanel.tsx**

```typescript
"use client";

import type { FailureCaseOut } from "@/app/document-qa/actions";
import { AlertTriangle } from "lucide-react";

interface FailureCasesPanelProps {
  failureCase: FailureCaseOut;
}

export function FailureCasesPanel({ failureCase }: FailureCasesPanelProps) {
  return (
    <div className="rounded-md border border-yellow-500/30 bg-yellow-500/5 p-3">
      <div className="mb-2 flex items-center gap-2 text-sm font-medium text-yellow-700">
        <AlertTriangle className="h-4 w-4" />
        Retrieval Failure Case
      </div>
      <div className="space-y-2 text-xs">
        <div>
          <span className="font-medium">Question:</span> {failureCase.question}
        </div>
        <div>
          <span className="font-medium">Expected:</span> {failureCase.expected_answer}
        </div>
        <div>
          <span className="font-medium">Retrieval Issue:</span> {failureCase.retrieval_issue}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 8: Commit**

```bash
git add frontend/components/document-qa/
git commit -m "feat: add Document QA frontend components"
```

---

### Task 11: Frontend page

**Files:**
- Create: `frontend/app/document-qa/page.tsx`

- [ ] **Step 1: Create page.tsx**

```typescript
"use client";

import { useState, useCallback } from "react";
import {
  uploadDocument,
  queryDocument,
  getSources,
  deleteSource,
  loadDemoScenario,
  type SourceOut,
  type QuestionResponse,
} from "./actions";
import type { DocumentQAStatus } from "@/types/ai";
import { DemoScenarios } from "@/components/document-qa/DemoScenarios";
import { DocumentUploader } from "@/components/document-qa/DocumentUploader";
import { SourcesList } from "@/components/document-qa/SourcesList";
import { QuestionInput } from "@/components/document-qa/QuestionInput";
import { AnswerCard } from "@/components/document-qa/AnswerCard";
import { ErrorState } from "@/components/ai/ErrorState";
import { Separator } from "@/components/ui/separator";

type Tab = "demo" | "upload";

export default function DocumentQAPage() {
  const [activeTab, setActiveTab] = useState<Tab>("demo");
  const [sources, setSources] = useState<SourceOut[]>([]);
  const [status, setStatus] = useState<DocumentQAStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QuestionResponse | null>(null);
  const [loadedScenario, setLoadedScenario] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleLoadScenario = useCallback(async (scenarioId: string) => {
    setStatus("loading");
    setError(null);
    setResponse(null);
    setLoadedScenario(scenarioId);

    try {
      const newSources = await loadDemoScenario(scenarioId);
      setSources((prev) => [...prev, ...newSources]);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scenario");
      setStatus("error");
      setLoadedScenario(null);
    }
  }, []);

  const handleQuestion = useCallback(async (question: string) => {
    setStatus("loading");
    setError(null);
    setResponse(null);

    try {
      const result = await queryDocument(question);
      setResponse(result);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to query documents");
      setStatus("error");
    }
  }, []);

  const handleUpload = useCallback(async (filename: string, content: string, contentType: string) => {
    setStatus("loading");
    setError(null);

    try {
      const source = await uploadDocument(filename, content, contentType);
      setSources((prev) => [...prev, source]);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload document");
      setStatus("error");
    }
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    setDeletingId(id);
    try {
      await deleteSource(id);
      setSources((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source");
    } finally {
      setDeletingId(null);
    }
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 space-y-1">
        <h1 className="text-2xl font-bold">Document QA</h1>
        <p className="text-muted-foreground">
          Upload documents and ask questions. Answers come with citations and source tracking.
        </p>
      </div>

      <div className="mb-6 flex gap-1 border-b">
        <button
          onClick={() => setActiveTab("demo")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "demo"
              ? "border-foreground text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Demo Scenarios
        </button>
        <button
          onClick={() => setActiveTab("upload")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "upload"
              ? "border-foreground text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          My Documents
        </button>
      </div>

      {activeTab === "demo" && (
        <div className="space-y-6">
          <DemoScenarios
            onLoad={handleLoadScenario}
            onQuestionClick={handleQuestion}
            loadedScenario={loadedScenario}
            loading={status === "loading"}
          />
        </div>
      )}

      {activeTab === "upload" && (
        <div className="space-y-6">
          <DocumentUploader
            onUpload={handleUpload}
            disabled={status === "loading"}
          />

          <Separator />

          <SourcesList
            sources={sources}
            onDelete={handleDelete}
            deleting={deletingId}
          />

          <QuestionInput
            onSubmit={handleQuestion}
            disabled={sources.length === 0}
            loading={status === "loading"}
          />
        </div>
      )}

      {status === "error" && (
        <div className="mt-6">
          <ErrorState
            message={error ?? "Something went wrong"}
            onRetry={() => {
              setStatus("idle");
              setError(null);
            }}
          />
        </div>
      )}

      {response && (
        <div className="mt-6">
          <AnswerCard response={response} />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/document-qa/page.tsx
git commit -m "feat: add Document QA page with demo and upload tabs"
```

---

### Task 12: Nav link

**Files:**
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Add Document QA link to nav**

Open `frontend/app/layout.tsx`. Add the link inside the `<nav>` element:

```tsx
<Link href="/document-qa" className="text-muted-foreground hover:text-foreground transition-colors">
  Document QA
</Link>
```

Place it after the Tool Playground link.

- [ ] **Step 2: Commit**

```bash
git add frontend/app/layout.tsx
git commit -m "feat: add Document QA to navigation"
```

---

## Verification

After all tasks are complete, run:

```bash
# Backend tests
cd backend && python -m pytest tests/test_documents.py -v

# Backend lint
cd backend && python -m pytest tests/ -v

# Frontend build check
cd frontend && npm run build
```

### Manual Checks

1. Start backend: `cd backend && uvicorn app.main:app --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to http://localhost:3000/document-qa
4. Click "Demo Scenarios" tab → click "Load Scenario" on any card
5. Click a predefined question → see answer with citations
6. For "Спроси по конспектам" and "Сравни 3 документа" — verify FailureCasesPanel appears
7. Switch to "My Documents" tab → upload a .md file → ask a question
8. Delete the source → verify list updates
