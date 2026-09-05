"""
Screening Repository — persistence layer for AI pipeline results.

Responsibilities:
  • Map Pydantic models → database tables
  • Persist screening results after the pipeline runs
  • Retrieve historical screenings for the dashboard
  • Gracefully no-op when the database is unavailable

Raw SQL in agents is forbidden — all DB access goes through this module.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.db.connection import DatabasePool
from app.schemas.models import (
    CandidateScore,
    GapAnalysis,
    MatchStatus,
    ScreeningResult,
    SkillMatch,
)

logger = logging.getLogger(__name__)


# ── enum mapping helpers ──────────────────────────────────────────

def _match_status_to_db(status: MatchStatus) -> str:
    """Map our MatchStatus → DB match_strength enum."""
    return {
        MatchStatus.MATCH: "exact",
        MatchStatus.PARTIAL_MATCH: "partial",
        MatchStatus.NO_EVIDENCE: "none",
    }[status]


def _score_to_recommendation(score: float) -> str:
    """Map numeric score → DB screening_recommendation enum."""
    if score >= 75:
        return "strong_match"
    if score >= 50:
        return "good_match"
    if score >= 30:
        return "partial_match"
    return "weak_match"


def _gap_severity_to_db(severity: str) -> str:
    """Map our GapSeverity → DB gap_severity enum."""
    return {
        "HIGH": "critical",
        "MEDIUM": "major",
        "LOW": "minor",
    }.get(severity.upper(), "minor")


class ScreeningRepository:
    """Read/write screening data against the teammate's PostgreSQL schema."""

    def __init__(self, pool: DatabasePool) -> None:
        self.pool = pool
        self.default_org_id = os.getenv(
            "DEFAULT_ORG_ID", "a0000000-0000-0000-0000-000000000001"
        )

    # ── write ──────────────────────────────────────────────────────

    def persist_screening(
        self,
        result: ScreeningResult,
        *,
        resume_text: str | None = None,
        job_description: str | None = None,
    ) -> Optional[str]:
        """
        Persist a pipeline result to the database.

        Returns the ``screening_results.id`` UUID string, or ``None``
        if persistence was skipped (DB unavailable).
        """
        if not self.pool.available:
            logger.info("Database unavailable — skipping persistence")
            return None

        with self.pool.get_connection() as conn:
            if conn is None:
                return None
            try:
                cur = conn.cursor()

                # Set RLS tenant context
                cur.execute(
                    "SET app.current_org_id = %s", (self.default_org_id,)
                )

                # 1. Candidate
                candidate_name = result.candidate.candidate_name or "Unknown"
                candidate_email = (
                    f"{candidate_name.lower().replace(' ', '.')}@screening.local"
                )
                cur.execute(
                    """
                    INSERT INTO candidates
                        (organization_id, email, full_name, status)
                    VALUES (%s, %s, %s, 'screened')
                    ON CONFLICT (organization_id, email)
                        DO UPDATE SET status   = 'screened',
                                      updated_at = now()
                    RETURNING id
                    """,
                    (self.default_org_id, candidate_email, candidate_name),
                )
                candidate_id = cur.fetchone()[0]

                # 2. Resume (structured analysis as JSONB, raw text omitted for PII)
                cur.execute(
                    """
                    INSERT INTO resumes
                        (candidate_id, file_name, parsed_data)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        candidate_id,
                        "screening_upload",
                        json.dumps(result.candidate.model_dump(), default=str),
                    ),
                )
                resume_id = cur.fetchone()[0]

                # 3. Job
                cur.execute(
                    """
                    INSERT INTO jobs
                        (organization_id, title, description, status)
                    VALUES (%s, %s, %s, 'open')
                    RETURNING id
                    """,
                    (
                        self.default_org_id,
                        result.job.job_title or "Untitled Position",
                        job_description,
                    ),
                )
                job_id = cur.fetchone()[0]

                # 4. Job requirements
                req_id_map: dict[str, str] = {}
                for req in result.job.required_skills + result.job.preferred_skills:
                    cur.execute(
                        """
                        INSERT INTO job_requirements
                            (job_id, requirement_type, description, is_mandatory)
                        VALUES (%s, 'skill', %s, %s)
                        RETURNING id
                        """,
                        (job_id, req.skill, req in result.job.required_skills),
                    )
                    req_id_map[req.skill.lower()] = str(cur.fetchone()[0])

                # 5. Screening result
                score = result.score
                screening_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO screening_results
                        (id, job_id, candidate_id,
                         overall_score, skill_match_score,
                         experience_match_score,
                         summary, recommendation, screened_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ai_agent')
                    """,
                    (
                        screening_id,
                        job_id,
                        candidate_id,
                        score.total_score,
                        score.breakdown.required_skill_score,
                        score.breakdown.experience_score,
                        result.report.summary,
                        _score_to_recommendation(score.total_score),
                    ),
                )

                # 6. Skill matches
                for match in result.matches:
                    req_db_id = req_id_map.get(match.skill.lower())
                    cur.execute(
                        """
                        INSERT INTO skill_matches
                            (screening_result_id, job_requirement_id,
                             match_strength, score, explanation)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            screening_id,
                            req_db_id,
                            _match_status_to_db(match.status),
                            match.confidence * 100,
                            "; ".join(e.text for e in match.evidence) or None,
                        ),
                    )

                # 7. Evidence items
                for match in result.matches:
                    for ev in match.evidence:
                        cur.execute(
                            """
                            INSERT INTO evidence_items
                                (screening_result_id, evidence_type,
                                 content, source_reference, confidence)
                            VALUES (%s, 'resume_excerpt', %s, %s, 'supported')
                            """,
                            (
                                screening_id,
                                ev.text,
                                f"Section: {ev.section}, Page: {ev.page}"
                                if ev.section
                                else None,
                            ),
                        )

                # 8. Gap analysis
                all_gaps = (
                    result.gaps.gaps
                    + result.gaps.partial_matches
                    + result.gaps.weak_areas
                )
                for gap in all_gaps:
                    req_db_id = req_id_map.get(gap.requirement.lower())
                    if not req_db_id:
                        continue
                    cur.execute(
                        """
                        INSERT INTO gap_analysis
                            (screening_result_id, job_requirement_id,
                             gap_type, severity, description, suggestion)
                        VALUES (%s, %s, 'missing_skill', %s, %s, %s)
                        """,
                        (
                            screening_id,
                            req_db_id,
                            _gap_severity_to_db(gap.severity.value),
                            gap.reason,
                            None,
                        ),
                    )

                conn.commit()
                logger.info("Screening persisted: %s", screening_id)
                return screening_id

            except Exception as exc:
                conn.rollback()
                logger.error("Failed to persist screening result: %s", exc)
                return None

    # ── read ───────────────────────────────────────────────────────

    def get_screening(self, screening_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a single screening record by UUID."""
        if not self.pool.available:
            return None

        with self.pool.get_connection() as conn:
            if conn is None:
                return None
            try:
                cur = conn.cursor()
                cur.execute(
                    "SET app.current_org_id = %s", (self.default_org_id,)
                )
                cur.execute(
                    """
                    SELECT sr.id, sr.overall_score, sr.skill_match_score,
                           sr.experience_match_score, sr.summary,
                           sr.recommendation, sr.screened_at,
                           c.full_name, c.email,
                           j.title
                    FROM screening_results sr
                    JOIN candidates c ON c.id = sr.candidate_id
                    JOIN jobs j       ON j.id = sr.job_id
                    WHERE sr.id = %s
                    """,
                    (screening_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "screening_id": str(row[0]),
                    "overall_score": float(row[1]) if row[1] else 0,
                    "skill_match_score": float(row[2]) if row[2] else 0,
                    "experience_match_score": float(row[3]) if row[3] else 0,
                    "summary": row[4] or "",
                    "recommendation": row[5] or "",
                    "screened_at": row[6].isoformat() if row[6] else "",
                    "candidate_name": row[7],
                    "candidate_email": row[8],
                    "job_title": row[9],
                }
            except Exception as exc:
                logger.error("Failed to fetch screening %s: %s", screening_id, exc)
                return None

    def list_screenings(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent screening summaries for the dashboard."""
        if not self.pool.available:
            return []

        with self.pool.get_connection() as conn:
            if conn is None:
                return []
            try:
                cur = conn.cursor()
                cur.execute(
                    "SET app.current_org_id = %s", (self.default_org_id,)
                )
                cur.execute(
                    """
                    SELECT sr.id, sr.overall_score, sr.recommendation,
                           sr.screened_at,
                           c.full_name, j.title
                    FROM screening_results sr
                    JOIN candidates c ON c.id = sr.candidate_id
                    JOIN jobs j       ON j.id = sr.job_id
                    ORDER BY sr.screened_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return [
                    {
                        "screening_id": str(r[0]),
                        "overall_score": float(r[1]) if r[1] else 0,
                        "recommendation": r[2] or "",
                        "screened_at": r[3].isoformat() if r[3] else "",
                        "candidate_name": r[4],
                        "job_title": r[5],
                    }
                    for r in cur.fetchall()
                ]
            except Exception as exc:
                logger.error("Failed to list screenings: %s", exc)
                return []
