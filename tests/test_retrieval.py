"""
Tests for the retrieval service (chunking + vector search).

These test the deterministic parts (chunking, cosine similarity)
without requiring a Gemini API key.
"""

import numpy as np
import pytest

from app.schemas.models import ResumeChunk, RetrievedChunk
from app.services.retrieval_service import RetrievalService, _detect_section


class TestSectionDetection:
    @pytest.mark.parametrize("header,expected", [
        ("Experience", "Experience"),
        ("EXPERIENCE:", "Experience"),
        ("Work Experience", "Experience"),
        ("Education", "Education"),
        ("Skills", "Skills"),
        ("Technical Skills", "Skills"),
        ("Certifications", "Certifications"),
        ("Projects", "Projects"),
        ("Summary", "Summary"),
        ("Random text", None),
    ])
    def test_detect_section(self, header, expected):
        assert _detect_section(header) == expected


class TestChunking:
    """Test chunking without embeddings (no API key needed)."""

    class FakeEmbeddingService:
        """Stub that returns zero vectors."""
        def embed_text(self, text):
            return [0.0] * 10
        def embed_texts(self, texts):
            return [[0.0] * 10 for _ in texts]

    @pytest.fixture
    def svc(self):
        return RetrievalService(self.FakeEmbeddingService())

    def test_basic_chunking(self, svc):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = svc.chunk_text(text)
        assert len(chunks) == 3
        assert chunks[0].text == "First paragraph."

    def test_section_labels(self, svc):
        text = "Experience\nWorked at ABC for 3 years.\n\nEducation\nB.Tech CS."
        chunks = svc.chunk_text(text)
        assert any(c.section == "Experience" for c in chunks)
        assert any(c.section == "Education" for c in chunks)

    def test_empty_text(self, svc):
        chunks = svc.chunk_text("")
        assert len(chunks) == 1  # At least one chunk guaranteed

    def test_large_paragraph_split(self, svc):
        text = "A" * 1000  # Single large paragraph
        chunks = svc.chunk_text(text, chunk_size=200, overlap=50)
        assert len(chunks) > 1
        assert all(len(c.text) <= 200 for c in chunks)


class TestCosineSimilarity:
    """Test retrieval with synthetic embeddings."""

    class MockEmbeddingService:
        def __init__(self):
            self._vectors = {}

        def set_vector(self, text, vec):
            self._vectors[text] = vec

        def embed_text(self, text):
            return self._vectors.get(text, [0.0] * 3)

        def embed_texts(self, texts):
            return [self.embed_text(t) for t in texts]

    def test_retrieve_most_similar(self):
        emb = self.MockEmbeddingService()
        svc = RetrievalService(emb)

        # Create chunks with known embeddings
        c1 = ResumeChunk(text="Python expert", section="Skills",
                         embedding=[1.0, 0.0, 0.0])
        c2 = ResumeChunk(text="Java developer", section="Skills",
                         embedding=[0.0, 1.0, 0.0])
        c3 = ResumeChunk(text="AWS cloud", section="Experience",
                         embedding=[0.0, 0.0, 1.0])

        # Query close to Python
        emb.set_vector("Python", [0.9, 0.1, 0.0])

        results = svc.retrieve_relevant_chunks("Python", [c1, c2, c3], top_k=2)
        assert len(results) > 0
        assert results[0].text == "Python expert"  # Most similar
        assert results[0].similarity_score > 0.5

    def test_retrieve_for_skills(self):
        emb = self.MockEmbeddingService()
        svc = RetrievalService(emb)

        chunks = [
            ResumeChunk(text="Used Python daily", section="Experience",
                        embedding=[1.0, 0.0, 0.0]),
            ResumeChunk(text="AWS deployment", section="Experience",
                        embedding=[0.0, 0.0, 1.0]),
        ]

        emb.set_vector("Python", [0.9, 0.1, 0.0])
        emb.set_vector("AWS", [0.0, 0.1, 0.9])

        evidence = svc.retrieve_for_skills(["Python", "AWS"], chunks, top_k=1)
        assert "Python" in evidence
        assert "AWS" in evidence
        assert evidence["Python"][0].text == "Used Python daily"
        assert evidence["AWS"][0].text == "AWS deployment"
