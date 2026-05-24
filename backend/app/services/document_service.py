import base64
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


def _extract_pdf_text(content: str) -> str:
    try:
        pdf_bytes = base64.b64decode(content)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        raise AppError(
            "PDF_PARSE_ERROR",
            "Failed to parse PDF file. Ensure the file is a valid PDF.",
            422,
        )


_sources: dict[str, dict[str, Any]] = {}
_restored = False


def _restore_sources() -> None:
    global _sources, _restored
    if _restored:
        return
    _restored = True
    try:
        from app.services.chroma_client import _get_chroma_client, _COLLECTION_NAME
        client = _get_chroma_client()
        col = client.get_collection(_COLLECTION_NAME)
        all_data = col.get(include=["metadatas"])
        if not all_data["metadatas"] or not all_data["ids"]:
            return
        seen: set[str] = set()
        for i, meta in enumerate(all_data["metadatas"]):
            if not meta or "source_id" not in meta:
                continue
            sid = meta["source_id"]
            if sid in seen:
                _sources[sid]["chunk_count"] += 1
                continue
            seen.add(sid)
            _sources[sid] = {
                "id": sid,
                "filename": meta.get("filename", "unknown"),
                "content_type": meta.get("content_type", "text/plain"),
                "chunk_count": 1,
                "created_at": datetime.fromisoformat(
                    meta.get("created_at", datetime.now(timezone.utc).isoformat())
                ),
            }
    except Exception:
        pass


class DocumentService:
    def __init__(self) -> None:
        self._llm_service: LLMService | None = None
        _restore_sources()

    def _get_llm(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service

    async def ingest(self, payload: SourceCreate) -> SourceOut:
        source_id = str(uuid.uuid4())
        content = payload.content

        if payload.content_type == "application/pdf":
            content = _extract_pdf_text(payload.content)

        if payload.content_type == "text/markdown":
            chunks = _chunk_markdown(content)
        else:
            chunks = _chunk_text(content)

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        chunk_records = [
            {
                "source_id": source_id,
                "filename": payload.filename,
                "chunk_position": i,
                "text": chunk,
                "content_type": payload.content_type,
                "created_at": now_iso,
            }
            for i, chunk in enumerate(chunks)
        ]

        add_chunks(chunk_records)

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
    global _sources, _restored
    _sources.clear()
    _restored = False
    clear_failure_cache()


def clear_failure_cache() -> None:
    global _FAILURES
    _FAILURES = None
