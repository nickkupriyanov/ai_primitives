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
