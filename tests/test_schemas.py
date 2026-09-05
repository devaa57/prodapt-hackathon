"""
Tests for Pydantic schema validation and edge cases.

Tests cover:
- Valid model construction
- Enum validation
- Malformed LLM response handling
- Hallucination prevention (NO_EVIDENCE vs false claims)
"""

import json

import pytest
from pydantic import ValidationError

from app.schemas.models import (
    CandidateReport,
    Evidence,
    Experience,
    Gap,
    GapAnalysis,
    GapSeverity,
    JobAnalysis,
    MatchingResult,
    MatchStatus,
    Requirement,
    ResumeAnalysis,
    SkillMatch,
)


class TestResumeAnalysis:
    def test_valid_construction(self):
        r = ResumeAnalysis(
            candidate_name="Test",
            skills=["Python"],
            experience=[Experience(role="Dev", company="X", years=2.0)],
        )
        assert r.candidate_name == "Test"
        assert len(r.skills) == 1

    def test_defaults(self):
        r = ResumeAnalysis()
        assert r.candidate_name == ""
        assert r.skills == []
        assert r.total_years_of_experience == 0.0

    def test_negative_experience_rejected(self):
        with pytest.raises(ValidationError):
            ResumeAnalysis(total_years_of_experience=-1.0)


class TestJobAnalysis:
    def test_importance_bounds(self):
        with pytest.raises(ValidationError):
            Requirement(skill="Python", importance=0)
        with pytest.raises(ValidationError):
            Requirement(skill="Python", importance=6)

    def test_valid_importance(self):
        r = Requirement(skill="Python", importance=5)
        assert r.importance == 5


class TestMatchStatus:
    def test_valid_statuses(self):
        for status in ["MATCH", "PARTIAL_MATCH", "NO_EVIDENCE"]:
            m = SkillMatch(skill="Test", status=status, confidence=0.5)
            assert m.status == MatchStatus(status)

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            SkillMatch(skill="Test", status="INVALID", confidence=0.5)


class TestSkillMatch:
    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            SkillMatch(skill="X", status="MATCH", confidence=1.5)
        with pytest.raises(ValidationError):
            SkillMatch(skill="X", status="MATCH", confidence=-0.1)


class TestGapSeverity:
    def test_valid_severities(self):
        for sev in ["HIGH", "MEDIUM", "LOW"]:
            g = Gap(requirement="X", status="MISSING", severity=sev, reason="Test")
            assert g.severity == GapSeverity(sev)


# ──────────────────────────────────────────────────────────────────
# Malformed LLM response simulation
# ──────────────────────────────────────────────────────────────────

class TestMalformedLLMResponse:
    """Simulate what happens when an LLM returns garbage JSON."""

    def test_missing_required_field(self):
        """SkillMatch without 'skill' field."""
        raw = '{"status": "MATCH", "confidence": 0.9}'
        with pytest.raises(ValidationError):
            SkillMatch.model_validate_json(raw)

    def test_extra_fields_ignored(self):
        raw = json.dumps({
            "skill": "Python",
            "status": "MATCH",
            "confidence": 0.9,
            "hallucinated_field": "should be ignored",
        })
        m = SkillMatch.model_validate_json(raw)
        assert m.skill == "Python"

    def test_completely_invalid_json(self):
        with pytest.raises(ValidationError):
            ResumeAnalysis.model_validate_json("this is not json at all")

    def test_wrong_type(self):
        raw = json.dumps({"candidate_name": 123, "skills": "not a list"})
        with pytest.raises(ValidationError):
            ResumeAnalysis.model_validate_json(raw)


# ──────────────────────────────────────────────────────────────────
# Hallucination prevention: NO_EVIDENCE contract
# ──────────────────────────────────────────────────────────────────

class TestHallucinationPrevention:
    """
    Scenario: JD requires AWS. Resume does NOT mention AWS.
    The system MUST produce status=NO_EVIDENCE, NOT a fabricated match.
    """

    def test_no_evidence_is_valid(self):
        m = SkillMatch(
            skill="AWS",
            status=MatchStatus.NO_EVIDENCE,
            confidence=0.0,
            evidence=[],
        )
        assert m.status == MatchStatus.NO_EVIDENCE
        assert m.confidence == 0.0
        assert len(m.evidence) == 0

    def test_no_evidence_serialisation(self):
        m = SkillMatch(skill="AWS", status=MatchStatus.NO_EVIDENCE, confidence=0.0)
        data = m.model_dump()
        assert data["status"] == "NO_EVIDENCE"

    def test_gap_uses_fair_language(self):
        """Gaps should use 'No evidence of' phrasing."""
        g = Gap(
            requirement="Kubernetes",
            status="MISSING",
            severity=GapSeverity.HIGH,
            reason="No evidence of Kubernetes found in the resume.",
        )
        assert "No evidence" in g.reason
        # Should NOT contain "lacks" or "does not know"
        assert "lacks" not in g.reason.lower()
        assert "does not know" not in g.reason.lower()


class TestScreeningResultSerialization:
    """Ensure the full result model serialises cleanly."""

    def test_round_trip(self, sample_resume_analysis, sample_job_analysis, strong_matches):
        from app.schemas.models import CandidateScore, ScoreBreakdown, ScreeningResult

        result = ScreeningResult(
            candidate=sample_resume_analysis,
            job=sample_job_analysis,
            matches=strong_matches.matches,
            gaps=GapAnalysis(),
            score=CandidateScore(
                total_score=85.0,
                breakdown=ScoreBreakdown(
                    required_skill_score=100.0,
                    experience_score=100.0,
                    semantic_score=70.0,
                    education_score=100.0,
                    preferred_skill_score=50.0,
                ),
                weights_used={"required_skills": 0.4, "experience": 0.25,
                              "semantic": 0.15, "education": 0.1, "preferred_skills": 0.1},
            ),
            report=CandidateReport(
                recommendation="Strong candidate",
                summary="Test summary",
            ),
        )
        json_str = result.model_dump_json()
        restored = ScreeningResult.model_validate_json(json_str)
        assert restored.score.total_score == 85.0
        assert restored.report.recommendation == "Strong candidate"
