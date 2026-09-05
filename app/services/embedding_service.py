"""
Embedding service — wraps Gemini text-embedding-004.

Provides simple single-text and batch-text embedding methods.
"""

from __future__ import annotations

import logging

from google import genai

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate text embeddings via the Gemini embedding model."""

    def __init__(self, client: genai.Client, model: str = "text-embedding-004") -> None:
        self.client = client
        self.model = model

    def embed_text(self, text: str) -> list[float]:
        """Return the embedding vector for a single text."""
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
        )
        return list(result.embeddings[0].values)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Return embedding vectors for a list of texts.

        Calls the API once per text. For hackathon-sized inputs
        (< 50 chunks) this is fast enough.
        """
        embeddings: list[list[float]] = []
        for text in texts:
            embeddings.append(self.embed_text(text))
        return embeddings
