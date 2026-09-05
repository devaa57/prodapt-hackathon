"""
Orchestration Pipeline

Executes the full screening flow:

  resume text + job description
  → Resume Analysis (Agent 1)
  → JD Analysis    (Agent 2)
  → Chunking + Embedding + Retrieval (RAG)
  → Skill Matching (Agent 3)
  → Gap Analysis   (Agent 4)
  → Deterministic Score
  → Report         (Agent 5)
  → ScreeningResult
"""

from __future__ import annotations

import logging

from app.agents.gap_agent import GapAgent
from app.agents.jd_agent import JDAgent
from app.agents.matching_agent import MatchingAgent
from app.agents.report_agent import ReportAgent
from app.agents.resume_agent import ResumeAgent
from app.schemas.models import ScreeningResult
from app.scoring.scorer import ScoringEngine
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class ScreeningPipeline:
    """
    End-to-end candidate-screening pipeline.

    Initialise once and call :meth:`screen` for each resume/JD pair.
    """

    def __init__(
        self,
        llm: LLMService | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.llm = llm or LLMService()

        # Services
        self.embedding_service = EmbeddingService(self.llm.client)
        self.retrieval_service = RetrievalService(self.embedding_service)

        # Agents (all share the same LLM service)
        self.resume_agent = ResumeAgent(self.llm)
        self.jd_agent = JDAgent(self.llm)
        self.matching_agent = MatchingAgent(self.llm)
        self.gap_agent = GapAgent(self.llm)
        self.report_agent = ReportAgent(self.llm)

        # Deterministic scorer
        self.scorer = ScoringEngine(weights=weights)

    def screen(
        self,
        resume_text: str = "",
        job_description: str = "",
        pages: list[Any] | None = None
    ) -> ScreeningResult:
        """
        Run the full pipeline and return a :class:`ScreeningResult`.

        Raises on LLM errors after exhausting retries.
        """
        if pages:
            from app.services.pdf_service import PDFService
            full_text = PDFService.pages_to_text(pages)
        elif resume_text:
            full_text = resume_text
        else:
            raise ValueError("Must provide either resume_text or pages.")

        # ── Step 1: Analyse resume ──────────────────────────────────
        logger.info("Step 1/7: Analysing resume …")
        resume = self.resume_agent.analyze(full_text)

        # ── Step 2: Analyse JD ──────────────────────────────────────
        logger.info("Step 2/7: Analysing job description …")
        job = self.jd_agent.analyze(job_description)

        # ── Step 3: Chunk & embed resume ────────────────────────────
        logger.info("Step 3/7: Chunking and embedding resume …")
        chunks = self.retrieval_service.chunk_text(text=full_text, pages=pages)
        self.retrieval_service.embed_chunks(chunks)

        # ── Step 4: Retrieve evidence for each skill ────────────────
        logger.info("Step 4/7: Retrieving evidence for skills …")
        all_skills = [r.skill for r in job.required_skills] + [
            r.skill for r in job.preferred_skills
        ]
        evidence_map = self.retrieval_service.retrieve_for_skills(
            skills=all_skills,
            chunks=chunks,
            top_k=3,
        )

        # ── Step 5: Skill matching ──────────────────────────────────
        logger.info("Step 5/7: Matching skills …")
        matches = self.matching_agent.match(resume, job, evidence_map)

        # ── Step 6: Gap analysis ────────────────────────────────────
        logger.info("Step 6/7: Analysing gaps …")
        gaps = self.gap_agent.analyze(job, resume, matches, evidence_map)

        # ── Step 7a: Deterministic scoring ──────────────────────────
        logger.info("Step 7/7: Scoring & generating report …")
        score = self.scorer.calculate_score(resume, job, matches, gaps)

        # ── Step 7b: Report ─────────────────────────────────────────
        report = self.report_agent.generate(resume, job, matches, gaps, score)

        return ScreeningResult(
            candidate=resume,
            job=job,
            matches=matches.matches,
            gaps=gaps,
            score=score,
            report=report,
        )
