"""
Retrieval service — chunking + in-memory vector search.

Implements the RAG layer for providing evidence to downstream agents.
The vector store is intentionally in-memory (numpy) so the prototype
runs immediately without pgvector / external DBs.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import numpy as np

from app.schemas.models import ResumeChunk, RetrievedChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# Common resume section headers (case-insensitive)
_SECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Summary",        re.compile(r"(?i)^(summary|objective|profile|about\s*me)")),
    ("Experience",     re.compile(r"(?i)^(experience|work\s*experience|employment|professional\s*experience)")),
    ("Education",      re.compile(r"(?i)^(education|academic|qualification)")),
    ("Skills",         re.compile(r"(?i)^(skills|technical\s*skills|core\s*competencies|competencies)")),
    ("Projects",       re.compile(r"(?i)^(projects|personal\s*projects|key\s*projects)")),
    ("Certifications", re.compile(r"(?i)^(certifications?|licenses?|accreditations?)")),
    ("Awards",         re.compile(r"(?i)^(awards?|honours?|honors?|achievements?)")),
    ("Publications",   re.compile(r"(?i)^(publications?|papers?|research)")),
]


def _detect_section(line: str) -> Optional[str]:
    """Return the section label if *line* looks like a section header."""
    stripped = line.strip().rstrip(":").strip()
    for label, pattern in _SECTION_PATTERNS:
        if pattern.match(stripped):
            return label
    return None


class RetrievalService:
    """Chunk text, embed chunks, and perform cosine-similarity retrieval."""

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service

    # ── chunking ───────────────────────────────────────────────────

    def chunk_text(
        self,
        text: str = "",
        pages: list[Any] | None = None,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[ResumeChunk]:
        """
        Split resume text into chunks, preserving section labels and page numbers.
        """
        chunks: list[ResumeChunk] = []
        current_section = ""

        # Normalize input into (page_num, text) tuples
        sources = []
        if pages:
            sources = [(p.page, p.text.strip()) for p in pages]
        elif text:
            sources = [(0, text.strip())]
            
        for page_num, content in sources:
            if not content:
                continue
                
            paragraphs = re.split(r"\n{2,}", content)
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Check if this paragraph is (or starts with) a section header
                first_line = para.split("\n", 1)[0]
                detected = _detect_section(first_line)
                if detected:
                    current_section = detected

                # Small paragraph → single chunk
                if len(para) <= chunk_size:
                    chunks.append(ResumeChunk(text=para, section=current_section, page=page_num))
                else:
                    # Sliding-window split
                    for start in range(0, len(para), chunk_size - overlap):
                        window = para[start : start + chunk_size]
                        if window.strip():
                            chunks.append(ResumeChunk(text=window, section=current_section, page=page_num))

        # Guarantee at least one chunk
        if not chunks:
            if pages:
                fallback = pages[0].text if pages[0].text else ""
                chunks.append(ResumeChunk(text=fallback[:chunk_size], section="", page=1))
            else:
                chunks.append(ResumeChunk(text=text[:chunk_size] if text else "", section="", page=0))

        return chunks

    # ── embedding ──────────────────────────────────────────────────

    def embed_chunks(self, chunks: list[ResumeChunk]) -> None:
        """Compute and attach embedding vectors to each chunk (in-place)."""
        texts = [c.text for c in chunks]
        if not texts:
            return
        vectors = self.embedding_service.embed_texts(texts)
        for chunk, vec in zip(chunks, vectors):
            chunk.embedding = vec

    # ── retrieval ──────────────────────────────────────────────────

    def retrieve_relevant_chunks(
        self,
        query: str,
        chunks: list[ResumeChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Return the *top_k* most similar chunks for a single query."""
        if not chunks or not chunks[0].embedding:
            return []

        query_vec = np.array(self.embedding_service.embed_text(query))
        chunk_matrix = np.array([c.embedding for c in chunks])

        # Cosine similarity
        norms = np.linalg.norm(chunk_matrix, axis=1) * np.linalg.norm(query_vec)
        norms = np.where(norms == 0, 1.0, norms)
        similarities = chunk_matrix @ query_vec / norms

        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [
            RetrievedChunk(
                text=chunks[i].text,
                section=chunks[i].section,
                page=chunks[i].page,
                similarity_score=round(float(similarities[i]), 4),
            )
            for i in top_indices
            if similarities[i] > 0.0
        ]

    def retrieve_for_skills(
        self,
        skills: list[str],
        chunks: list[ResumeChunk],
        top_k: int = 3,
    ) -> dict[str, list[RetrievedChunk]]:
        """
        Batch-retrieve evidence for every skill.

        Returns a dict mapping skill name → list[RetrievedChunk].
        """
        if not chunks or not chunks[0].embedding:
            return {skill: [] for skill in skills}

        chunk_matrix = np.array([c.embedding for c in chunks])
        chunk_norms = np.linalg.norm(chunk_matrix, axis=1)

        # Embed all skill queries in one batch
        skill_vectors = self.embedding_service.embed_texts(skills)

        evidence_map: dict[str, list[RetrievedChunk]] = {}
        for skill, skill_vec in zip(skills, skill_vectors):
            sv = np.array(skill_vec)
            norms = chunk_norms * np.linalg.norm(sv)
            norms = np.where(norms == 0, 1.0, norms)
            sims = chunk_matrix @ sv / norms

            top_idx = np.argsort(sims)[::-1][:top_k]
            evidence_map[skill] = [
                RetrievedChunk(
                    text=chunks[i].text,
                    section=chunks[i].section,
                    page=chunks[i].page,
                    similarity_score=round(float(sims[i]), 4),
                )
                for i in top_idx
                if sims[i] > 0.0
            ]

        return evidence_map
