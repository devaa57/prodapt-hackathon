"""
Deterministic Scoring Engine

The LLM does NOT decide the final score.
All weights are configurable and the calculation is pure Python.
"""

from __future__ import annotations

from app.schemas.models import (
    CandidateScore,
    GapAnalysis,
    JobAnalysis,
    MatchingResult,
    MatchStatus,
    ResumeAnalysis,
    ScoreBreakdown,
)

# Default weight configuration (must sum to 1.0)
DEFAULT_WEIGHTS: dict[str, float] = {
    "required_skills": 0.40,
    "experience": 0.25,
    "semantic": 0.15,
    "education": 0.10,
    "preferred_skills": 0.10,
}


class ScoringEngine:
    """Compute a deterministic 0-100 candidate score."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS.copy()

    # ── public API ─────────────────────────────────────────────────

    def calculate_score(
        self,
        resume: ResumeAnalysis,
        job: JobAnalysis,
        matches: MatchingResult,
        gaps: GapAnalysis,
    ) -> CandidateScore:
        req_score = self._score_required_skills(job, matches)
        exp_score = self._score_experience(resume, job)
        sem_score = self._score_semantic(matches)
        edu_score = self._score_education(resume, job)
        pref_score = self._score_preferred_skills(job, matches)

        total = (
            self.weights["required_skills"] * req_score
            + self.weights["experience"] * exp_score
            + self.weights["semantic"] * sem_score
            + self.weights["education"] * edu_score
            + self.weights["preferred_skills"] * pref_score
        )

        return CandidateScore(
            total_score=round(total, 2),
            breakdown=ScoreBreakdown(
                required_skill_score=round(req_score, 2),
                experience_score=round(exp_score, 2),
                semantic_score=round(sem_score, 2),
                education_score=round(edu_score, 2),
                preferred_skill_score=round(pref_score, 2),
            ),
            weights_used=self.weights,
        )

    # ── component scorers ──────────────────────────────────────────

    def _score_required_skills(self, job: JobAnalysis, matches: MatchingResult) -> float:
        """
        Importance-weighted skill score for required skills.

        MATCH = 1.0, PARTIAL_MATCH = 0.5, NO_EVIDENCE = 0.0
        """
        if not job.required_skills:
            return 100.0

        match_lookup = {m.skill.lower(): m for m in matches.matches}
        weighted_sum = 0.0
        weight_total = 0.0

        for req in job.required_skills:
            importance = req.importance
            weight_total += importance
            match = match_lookup.get(req.skill.lower())
            if match:
                if match.status == MatchStatus.MATCH:
                    weighted_sum += importance * 1.0
                elif match.status == MatchStatus.PARTIAL_MATCH:
                    weighted_sum += importance * 0.5
                # NO_EVIDENCE → 0.0

        if weight_total == 0:
            return 100.0
        return (weighted_sum / weight_total) * 100.0

    def _score_experience(self, resume: ResumeAnalysis, job: JobAnalysis) -> float:
        """Score based on years of experience vs minimum requirement."""
        required = job.minimum_experience_years
        if required <= 0:
            return 100.0

        candidate = resume.total_years_of_experience
        if candidate >= required:
            return 100.0

        return (candidate / required) * 100.0

    def _score_semantic(self, matches: MatchingResult) -> float:
        """
        Average confidence across all match assessments × 100.

        This uses the per-skill confidence the LLM assigned based on
        evidence quality — the aggregation into a single number is
        deterministic Python.
        """
        if not matches.matches:
            return 0.0
        total_conf = sum(m.confidence for m in matches.matches)
        return (total_conf / len(matches.matches)) * 100.0

    def _score_education(self, resume: ResumeAnalysis, job: JobAnalysis) -> float:
        """
        Simple keyword overlap between candidate education and JD requirements.

        Each JD education requirement is checked for a case-insensitive
        substring match against any of the candidate's education entries.
        """
        if not job.education_requirements:
            return 100.0

        if not resume.education:
            return 0.0

        matched = 0
        resume_edu_lower = [e.lower() for e in resume.education]

        for req in job.education_requirements:
            req_lower = req.lower()
            # Check if any education entry contains the requirement keywords
            for edu in resume_edu_lower:
                if req_lower in edu or edu in req_lower:
                    matched += 1
                    break
            else:
                # Try keyword overlap: split requirement into words and
                # check if the majority appear in any education entry
                req_words = set(req_lower.split())
                for edu in resume_edu_lower:
                    edu_words = set(edu.split())
                    overlap = req_words & edu_words
                    if len(overlap) >= len(req_words) * 0.5:
                        matched += 1
                        break

        return (matched / len(job.education_requirements)) * 100.0

    def _score_preferred_skills(self, job: JobAnalysis, matches: MatchingResult) -> float:
        """Same logic as required skills but for preferred skills."""
        if not job.preferred_skills:
            return 100.0  # No preferred skills → no penalty

        match_lookup = {m.skill.lower(): m for m in matches.matches}
        weighted_sum = 0.0
        weight_total = 0.0

        for req in job.preferred_skills:
            importance = req.importance
            weight_total += importance
            match = match_lookup.get(req.skill.lower())
            if match:
                if match.status == MatchStatus.MATCH:
                    weighted_sum += importance * 1.0
                elif match.status == MatchStatus.PARTIAL_MATCH:
                    weighted_sum += importance * 0.5

        if weight_total == 0:
            return 100.0
        return (weighted_sum / weight_total) * 100.0
