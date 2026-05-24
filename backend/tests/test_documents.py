import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
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
        type("Choice", (), {"message": type("Msg", (), {"content": "FastAPI is fast."})()})()
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
