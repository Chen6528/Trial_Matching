"""OpenAI text-embedding-3-small wrapper (1536-dim vectors)."""
from __future__ import annotations

from app.config import get_settings
from app.deps import get_openai


async def embed_texts(texts: list[str]) -> list[list[float]]:
    client = get_openai()
    resp = await client.embeddings.create(model=get_settings().embedding_model, input=texts)
    return [d.embedding for d in resp.data]


async def embed_text(text: str) -> list[float]:
    return (await embed_texts([text]))[0]
