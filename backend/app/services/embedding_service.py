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
