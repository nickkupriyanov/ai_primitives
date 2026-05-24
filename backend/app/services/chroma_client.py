import hashlib
import math
import os
import re
import uuid
from typing import Any

import chromadb
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions

from app.config import get_settings


_COLLECTION_NAME = "documents"
_CLIENT: ClientAPI | None = None
_EMBEDDING_DIMENSIONS = 1536
_EMBEDDING_FN: Any | None = None


class LocalHashEmbeddingFunction:
    def __call__(self, input: list[str]) -> list[list[float]]:
        return [_local_hash_embedding(text) for text in input]


def _local_hash_embedding(text: str) -> list[float]:
    vector = [0.0] * _EMBEDDING_DIMENSIONS
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % _EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector


def _has_openai_key(api_key: str | None) -> bool:
    return bool(api_key and api_key != "your_openai_api_key_here")


def _build_embedding_function() -> Any:
    settings = get_settings()
    if not _has_openai_key(settings.openai_api_key):
        return LocalHashEmbeddingFunction()
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        api_base=settings.openai_base_url,
        model_name="text-embedding-3-small",
    )


def _embed_texts(texts: list[str]) -> list[list[float]]:
    global _EMBEDDING_FN
    if _EMBEDDING_FN is None:
        _get_chroma_client()
    try:
        return _EMBEDDING_FN(texts)
    except Exception:
        _EMBEDDING_FN = LocalHashEmbeddingFunction()
        return _EMBEDDING_FN(texts)


def _get_chroma_client() -> ClientAPI:
    global _CLIENT, _EMBEDDING_FN
    if _CLIENT is not None:
        return _CLIENT

    persist_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "chroma"
    )
    os.makedirs(persist_dir, exist_ok=True)

    _EMBEDDING_FN = _build_embedding_function()

    _CLIENT = chromadb.PersistentClient(path=persist_dir)
    _CLIENT.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _CLIENT


def _collection():
    client = _get_chroma_client()
    try:
        return client.get_collection(_COLLECTION_NAME)
    except Exception:
        return _CLIENT.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )


def add_chunks(chunks: list[dict[str, Any]]) -> list[str]:
    if not chunks:
        return []
    chunk_ids = [str(uuid.uuid4()) for _ in chunks]
    documents = [c["text"] for c in chunks]
    _collection().add(
        ids=chunk_ids,
        documents=documents,
        embeddings=_embed_texts(documents),
        metadatas=[
            {
                "source_id": c["source_id"],
                "filename": c["filename"],
                "chunk_position": c["chunk_position"],
                "content_type": c.get("content_type", "text/plain"),
                "created_at": c.get("created_at", ""),
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
        query_embeddings=_embed_texts([query_text]),
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


def get_all_source_ids() -> list[str]:
    col = _collection()
    try:
        all_data = col.get(include=["metadatas"])
        if all_data["metadatas"]:
            return list({m["source_id"] for m in all_data["metadatas"] if m and "source_id" in m})
    except Exception:
        pass
    return []


def reset_for_tests() -> None:
    global _CLIENT, _EMBEDDING_FN
    if _CLIENT is not None:
        try:
            _CLIENT.delete_collection(_COLLECTION_NAME)
        except Exception:
            pass
        _CLIENT = None
        _EMBEDDING_FN = None
