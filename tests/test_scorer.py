"""
Tests for the deterministic scoring engine.

These run without any LLM calls — the scorer is pure Python.
"""

import pytest

from app.schemas.models import (
    CandidateScore,
    GapAnalysis,
    JobAnalysis,
    MatchingResult,
    MatchStatus,
    Requirement,
    ResumeAnalysis,
    ScoreBreakdown,
    SkillMatch,
)
from app.scoring.scorer import ScoringEngine


@pytest.fixture
def scorer() -> ScoringEngine:
    return ScoringEngine()


# ──────────────────────────────────────────────────────────────────
# 1. Strong candidate — all skills matched
# ──────────────────────────────────────────────────────────────────

class TestStrongCandidate:
    def test_high_total_score(
        self, scorer, sample_resume_analysis, sample_job_analysis,
        strong_matches, empty_gap_analysis,
    ):
        score = scorer.calculate_score(
            sample_resume_analysis, sample_job_analysis,
            strong_matches, empty_gap_analysis,
        )
        assert score.total_score >= 80.0, (
            f"Strong candidate should score ≥80, got {score.total_score}"
        )

    def test_required_skills_perfect(
        self, scorer, sample_resume_analysis, sample_job_analysis,
        strong_matches, empty_gap_analysis,
    ):
        score = scorer.calculate_score(
            sample_resume_analysis, sample_job_analysis,
            strong_matches, empty_gap_analysis,
        )
        assert score.breakdown.required_skill_score == 100.0

    def test_experience_full_marks(
        self, scorer, sample_resume_analysis, sample_job_analysis,
        strong_matches, empty_gap_analysis,
    ):
        score = scorer.calculate_score(
            sample_resume_analysis, sample_job_analysis,
            strong_matches, empty_gap_analysis,
        )
        # 5 years >= 3 years required
        assert score.breakdown.experience_score == 100.0


# ──────────────────────────────────────────────────────────────────
# 2. Partial candidate — some skills missing
# ──────────────────────────────────────────────────────────────────

class TestPartialCandidate:
    def test_moderate_score(
        self, scorer, sample_job_analysis, partial_matches, empty_gap_analysis,
    ):
        resume = ResumeAnalysis(
            candidate_name="Priya",
            total_years_of_experience=3.0,
            education=["B.Sc in Information Technology"],
        )
        score = scorer.calculate_score(
            resume, sample_job_analysis, partial_matches, empty_gap_analysis,
        )
        assert 30.0 <= score.total_score <= 75.0, (
            f"Partial candidate should score 30-75, got {score.total_score}"
        )


# ──────────────────────────────────────────────────────────────────
# 3. Candidate with major gaps
# ──────────────────────────────────────────────────────────────────

class TestMajorGaps:
    def test_low_score(self, scorer, sample_job_analysis, empty_gap_analysis):
        resume = ResumeAnalysis(
            candidate_name="Amit",
            total_years_of_experience=1.0,
            education=["Diploma in Computer Applications"],
        )
        no_matches = MatchingResult(
            matches=[
                SkillMatch(skill="Python", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
                SkillMatch(skill="TensorFlow", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
                SkillMatch(skill="AWS", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
                SkillMatch(skill="SQL", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
                SkillMatch(skill="Machine Learning", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
            ]
        )
        score = scorer.calculate_score(
            resume, sample_job_analysis, no_matches, empty_gap_analysis,
        )
        assert score.total_score < 30.0, (
            f"Candidate with major gaps should score <30, got {score.total_score}"
        )


# ──────────────────────────────────────────────────────────────────
# 4. Missing skill → NO_EVIDENCE (not zero skill score fabrication)
# ──────────────────────────────────────────────────────────────────

class TestNoEvidenceHandling:
    """JD requires AWS. Resume doesn't mention AWS. Expected: NO_EVIDENCE, not negative."""

    def test_no_evidence_does_not_fabricate(self, scorer):
        job = JobAnalysis(
            job_title="Cloud Engineer",
            required_skills=[Requirement(skill="AWS", importance=5)],
        )
        resume = ResumeAnalysis(candidate_name="Test", total_years_of_experience=5.0)

        matches = MatchingResult(
            matches=[
                SkillMatch(skill="AWS", status=MatchStatus.NO_EVIDENCE, confidence=0.0)
            ]
        )
        score = scorer.calculate_score(resume, job, matches, GapAnalysis())

        # The required_skill_score should be 0 (no evidence), not negative
        assert score.breakdown.required_skill_score == 0.0
        # But experience should still count
        assert score.breakdown.experience_score == 100.0
        # Total should not be negative
        assert score.total_score >= 0.0


# ──────────────────────────────────────────────────────────────────
# 5. Missing experience
# ──────────────────────────────────────────────────────────────────

class TestExperienceScoring:
    def test_exact_match(self, scorer, sample_job_analysis):
        resume = ResumeAnalysis(total_years_of_experience=3.0)
        matches = MatchingResult()
        score = scorer.calculate_score(resume, sample_job_analysis, matches, GapAnalysis())
        assert score.breakdown.experience_score == 100.0

    def test_exceeds_requirement(self, scorer, sample_job_analysis):
        resume = ResumeAnalysis(total_years_of_experience=10.0)
        matches = MatchingResult()
        score = scorer.calculate_score(resume, sample_job_analysis, matches, GapAnalysis())
        assert score.breakdown.experience_score == 100.0

    def test_below_requirement(self, scorer, sample_job_analysis):
        resume = ResumeAnalysis(total_years_of_experience=1.5)
        matches = MatchingResult()
        score = scorer.calculate_score(resume, sample_job_analysis, matches, GapAnalysis())
        assert score.breakdown.experience_score == 50.0  # 1.5 / 3.0 * 100

    def test_zero_experience(self, scorer, sample_job_analysis):
        resume = ResumeAnalysis(total_years_of_experience=0.0)
        matches = MatchingResult()
        score = scorer.calculate_score(resume, sample_job_analysis, matches, GapAnalysis())
        assert score.breakdown.experience_score == 0.0

    def test_no_requirement(self, scorer):
        job = JobAnalysis(job_title="Open Role", minimum_experience_years=0.0)
        resume = ResumeAnalysis(total_years_of_experience=0.0)
        matches = MatchingResult()
        score = scorer.calculate_score(resume, job, matches, GapAnalysis())
        assert score.breakdown.experience_score == 100.0


# ──────────────────────────────────────────────────────────────────
# 6. Weight configuration
# ──────────────────────────────────────────────────────────────────

class TestConfigurableWeights:
    def test_custom_weights(self):
        custom = {
            "required_skills": 0.50,
            "experience": 0.20,
            "semantic": 0.10,
            "education": 0.10,
            "preferred_skills": 0.10,
        }
        scorer = ScoringEngine(weights=custom)
        assert scorer.weights == custom

    def test_weights_affect_score(self, sample_resume_analysis, sample_job_analysis,
                                   strong_matches, empty_gap_analysis):
        # All experience weight → score depends entirely on experience
        scorer_exp = ScoringEngine(weights={
            "required_skills": 0.0,
            "experience": 1.0,
            "semantic": 0.0,
            "education": 0.0,
            "preferred_skills": 0.0,
        })
        score = scorer_exp.calculate_score(
            sample_resume_analysis, sample_job_analysis,
            strong_matches, empty_gap_analysis,
        )
        assert score.total_score == 100.0  # 5 years >= 3 years required


# ──────────────────────────────────────────────────────────────────
# 7. Edge cases
# ──────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_job(self, scorer):
        """No requirements → all component scores are 100 except semantic (no matches → 0)."""
        job = JobAnalysis(job_title="Any")
        resume = ResumeAnalysis(candidate_name="Test")
        score = scorer.calculate_score(resume, job, MatchingResult(), GapAnalysis())
        # semantic_score = 0 (no matches to derive confidence from)
        # total = 0.40*100 + 0.25*100 + 0.15*0 + 0.10*100 + 0.10*100 = 85.0
        assert score.total_score == 85.0
        assert score.breakdown.required_skill_score == 100.0
        assert score.breakdown.semantic_score == 0.0

    def test_score_is_bounded(self, scorer, sample_resume_analysis, sample_job_analysis,
                               strong_matches, empty_gap_analysis):
        score = scorer.calculate_score(
            sample_resume_analysis, sample_job_analysis,
            strong_matches, empty_gap_analysis,
        )
        assert 0.0 <= score.total_score <= 100.0

    def test_weights_in_output(self, scorer, sample_resume_analysis, sample_job_analysis,
                                strong_matches, empty_gap_analysis):
        score = scorer.calculate_score(
            sample_resume_analysis, sample_job_analysis,
            strong_matches, empty_gap_analysis,
        )
        assert "required_skills" in score.weights_used
        assert abs(sum(score.weights_used.values()) - 1.0) < 1e-6
