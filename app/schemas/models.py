"""
Pydantic models for every structured input/output in the screening pipeline.

All LLM agent outputs are validated against these schemas.
Invalid responses trigger controlled retries.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Resume Analysis (Agent 1)
# ──────────────────────────────────────────────

class Experience(BaseModel):
    """A single work-experience entry extracted from the resume."""
    role: str = Field(description="Job title / role held")
    company: str = Field(description="Employer or organisation name")
    years: float = Field(
        default=0.0,
        ge=0.0,
        description="Duration in years (estimate conservatively if dates are unclear)",
    )
    skills_used: list[str] = Field(
        default_factory=list,
        description="Skills explicitly mentioned in this role's description",
    )
    description: str = Field(
        default="",
        description="Brief summary of responsibilities / achievements",
    )


class Project(BaseModel):
    """A project entry extracted from the resume."""
    name: str = Field(description="Project name or title")
    description: str = Field(default="", description="What the project does / achieved")
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies / tools explicitly mentioned",
    )


class ResumeAnalysis(BaseModel):
    """
    Structured extraction from a raw resume.

    RULE: Only include information **explicitly stated** in the resume.
    Do NOT infer or fabricate missing fields.
    """
    candidate_name: str = Field(default="", description="Full name of the candidate")
    skills: list[str] = Field(
        default_factory=list,
        description="All skills mentioned anywhere in the resume",
    )
    technical_skills: list[str] = Field(
        default_factory=list,
        description="Technical / hard skills (languages, tools, frameworks)",
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Soft skills (leadership, communication, etc.)",
    )
    experience: list[Experience] = Field(default_factory=list)
    total_years_of_experience: float = Field(
        default=0.0,
        ge=0.0,
        description="Total professional experience in years",
    )
    education: list[str] = Field(
        default_factory=list,
        description="Degrees / diplomas exactly as stated",
    )
    certifications: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Job-Description Analysis (Agent 2)
# ──────────────────────────────────────────────

class Requirement(BaseModel):
    """A single skill / requirement with an importance weight."""
    skill: str = Field(description="Skill or requirement name")
    importance: int = Field(
        ge=1,
        le=5,
        description="Importance weight: 1 = nice-to-know … 5 = critical",
    )


class JobAnalysis(BaseModel):
    """Structured extraction from a raw Job Description."""
    job_title: str = Field(default="", description="Title of the open position")
    required_skills: list[Requirement] = Field(
        default_factory=list,
        description="Must-have skills/requirements",
    )
    preferred_skills: list[Requirement] = Field(
        default_factory=list,
        description="Nice-to-have skills/requirements",
    )
    minimum_experience_years: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum years of professional experience required",
    )
    education_requirements: list[str] = Field(
        default_factory=list,
        description="Required education qualifications",
    )
    other_requirements: list[str] = Field(
        default_factory=list,
        description="Any other stated requirements (e.g. security clearance)",
    )


# ──────────────────────────────────────────────
# Skill Matching (Agent 3)
# ──────────────────────────────────────────────

class MatchStatus(str, Enum):
    """
    MATCH          – clear evidence the candidate possesses the skill.
    PARTIAL_MATCH  – related but not exact evidence found.
    NO_EVIDENCE    – the resume simply does not mention this skill.
                     This is NOT the same as "candidate lacks the skill".
    """
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_EVIDENCE = "NO_EVIDENCE"


class Evidence(BaseModel):
    """A supporting snippet from the resume."""
    text: str = Field(description="Exact or near-exact quote from the resume")
    section: str = Field(default="", description="Resume section (e.g. Experience, Skills)")
    page: int = Field(default=0, ge=0, description="Page number if available")


class SkillMatch(BaseModel):
    """Result of comparing one JD requirement against the resume."""
    skill: str = Field(description="The requirement being evaluated")
    status: MatchStatus = Field(description="Classification of match quality")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the classification (0.0 – 1.0)",
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Supporting evidence from the resume",
    )


class MatchingResult(BaseModel):
    """Wrapper returned by the matching agent."""
    matches: list[SkillMatch] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Gap Analysis (Agent 4)
# ──────────────────────────────────────────────

class GapSeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Gap(BaseModel):
    """A single identified gap between the candidate and the JD."""
    requirement: str = Field(description="The JD requirement")
    status: str = Field(description="e.g. MISSING, PARTIAL, WEAK")
    severity: GapSeverity = Field(description="Impact severity")
    reason: str = Field(
        description=(
            "Explanation – MUST use phrasing like "
            "'No evidence of X found in the resume' "
            "rather than 'candidate does not know X'."
        ),
    )


class GapAnalysis(BaseModel):
    """Aggregated gap-analysis output."""
    gaps: list[Gap] = Field(default_factory=list, description="Missing requirements")
    partial_matches: list[Gap] = Field(
        default_factory=list,
        description="Requirements with partial evidence",
    )
    weak_areas: list[Gap] = Field(
        default_factory=list,
        description="Areas where the candidate is below expectation",
    )


# ──────────────────────────────────────────────
# Deterministic Scoring
# ──────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    """Individual component scores (each 0-100)."""
    required_skill_score: float = Field(default=0.0)
    experience_score: float = Field(default=0.0)
    semantic_score: float = Field(default=0.0)
    education_score: float = Field(default=0.0)
    preferred_skill_score: float = Field(default=0.0)


class CandidateScore(BaseModel):
    """Final deterministic score with full breakdown."""
    total_score: float = Field(description="Weighted total (0-100)")
    breakdown: ScoreBreakdown
    weights_used: dict[str, float] = Field(
        description="Weight configuration that produced this score",
    )


# ──────────────────────────────────────────────
# Report (Agent 5)
# ──────────────────────────────────────────────

class CandidateReport(BaseModel):
    """Recruiter-friendly final report."""
    recommendation: str = Field(
        description="e.g. Strong candidate, Moderate fit, Weak fit",
    )
    summary: str = Field(description="Concise candidate evaluation narrative")
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(
        default_factory=list,
        description="Suggested interview topics to probe gaps",
    )


# ──────────────────────────────────────────────
# Retrieval / Chunking (internal)
# ──────────────────────────────────────────────

class ResumeChunk(BaseModel):
    """An internal chunk of resume text with its embedding vector."""
    text: str
    section: str = ""
    page: int = 0
    embedding: list[float] = Field(default_factory=list, exclude=True)


class RetrievedChunk(BaseModel):
    """A chunk returned by the retrieval layer with similarity metadata."""
    text: str
    section: str = ""
    page: int = 0
    similarity_score: float = Field(default=0.0, ge=0.0)


# ──────────────────────────────────────────────
# API request / response
# ──────────────────────────────────────────────

class ScreeningRequest(BaseModel):
    """POST /screen request body."""
    job_description: str = Field(description="Raw job-description text")
    resume_text: str = Field(description="Raw resume text")


class ScreeningResult(BaseModel):
    """Complete screening response returned by POST /screen."""
    screening_id: Optional[str] = Field(
        default=None,
        description="Database UUID — populated when the result is persisted",
    )
    candidate: ResumeAnalysis
    job: JobAnalysis
    matches: list[SkillMatch]
    gaps: GapAnalysis
    score: CandidateScore
    report: CandidateReport


class ScreeningRecord(BaseModel):
    """Lightweight screening summary retrieved from the database."""
    screening_id: str
    candidate_name: str
    candidate_email: str = ""
    job_title: str
    overall_score: float = 0.0
    skill_match_score: float = 0.0
    experience_match_score: float = 0.0
    summary: str = ""
    recommendation: str = ""
    screened_at: str = ""

