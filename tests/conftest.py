"""
Shared fixtures for the test suite.
"""

import pytest

from app.schemas.models import (
    CandidateScore,
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
    ScoreBreakdown,
    SkillMatch,
)


# ── Sample resume text ─────────────────────────────────────────────

STRONG_RESUME = """\
Rahul Sharma
Senior Machine Learning Engineer

Summary
Experienced ML engineer with 5+ years building production ML systems.

Experience

Senior ML Engineer — TechCorp (2021–present, 3 years)
- Built real-time recommendation engine serving 10M users using Python and TensorFlow.
- Deployed ML inference services on AWS EC2 and S3 with CI/CD pipelines.
- Led a team of 4 engineers; mentored junior developers.

ML Engineer — DataLabs (2019–2021, 2 years)
- Developed NLP pipelines for sentiment analysis using Python and spaCy.
- Managed data pipelines on AWS Glue and Redshift.
- Collaborated with product teams to define KPIs.

Skills
Python, TensorFlow, PyTorch, SQL, AWS (EC2, S3, Glue, Redshift), Docker, Kubernetes,
scikit-learn, spaCy, Git, CI/CD, Linux

Education
B.Tech in Computer Science — IIT Bombay (2019)

Certifications
AWS Certified Solutions Architect – Associate
"""

PARTIAL_RESUME = """\
Priya Desai
Software Developer

Experience

Software Developer — WebWorks (2022–present, 2 years)
- Built REST APIs using Python and Flask.
- Wrote SQL queries for PostgreSQL databases.
- Participated in code reviews.

Intern — StartupXYZ (2021–2022, 1 year)
- Assisted in building a dashboard using React and Node.js.

Skills
Python, Flask, SQL, PostgreSQL, React, Node.js, Git

Education
B.Sc in Information Technology — Mumbai University (2021)
"""

WEAK_RESUME = """\
Amit Patel
Junior Developer

Experience

Junior Developer — LocalTech (2023–present, 1 year)
- Maintained legacy PHP applications.
- Fixed bugs in WordPress sites.

Skills
PHP, WordPress, HTML, CSS, JavaScript, MySQL

Education
Diploma in Computer Applications — State Polytechnic (2022)
"""

SAMPLE_JD = """\
Senior Machine Learning Engineer

We are looking for a Senior ML Engineer to join our AI team.

Requirements:
- 3+ years of experience in machine learning
- Strong proficiency in Python
- Experience with deep learning frameworks (TensorFlow or PyTorch)
- Experience with AWS cloud services
- SQL and data pipeline experience
- Bachelor's degree in Computer Science or related field

Preferred:
- Experience with Kubernetes and Docker
- NLP experience
- Published ML research or patents
"""


# ── Pre-built fixtures ─────────────────────────────────────────────

@pytest.fixture
def sample_resume_analysis() -> ResumeAnalysis:
    return ResumeAnalysis(
        candidate_name="Rahul Sharma",
        skills=["Python", "TensorFlow", "PyTorch", "SQL", "AWS", "Docker", "Kubernetes"],
        technical_skills=["Python", "TensorFlow", "PyTorch", "SQL", "AWS", "Docker", "Kubernetes"],
        soft_skills=["Leadership", "Mentoring"],
        experience=[
            Experience(role="Senior ML Engineer", company="TechCorp", years=3.0,
                       skills_used=["Python", "TensorFlow", "AWS"]),
            Experience(role="ML Engineer", company="DataLabs", years=2.0,
                       skills_used=["Python", "spaCy", "AWS"]),
        ],
        total_years_of_experience=5.0,
        education=["B.Tech in Computer Science"],
        certifications=["AWS Certified Solutions Architect"],
        projects=[],
    )


@pytest.fixture
def sample_job_analysis() -> JobAnalysis:
    return JobAnalysis(
        job_title="Senior Machine Learning Engineer",
        required_skills=[
            Requirement(skill="Python", importance=5),
            Requirement(skill="TensorFlow", importance=4),
            Requirement(skill="AWS", importance=4),
            Requirement(skill="SQL", importance=3),
            Requirement(skill="Machine Learning", importance=5),
        ],
        preferred_skills=[
            Requirement(skill="Kubernetes", importance=2),
            Requirement(skill="Docker", importance=2),
            Requirement(skill="NLP", importance=3),
        ],
        minimum_experience_years=3.0,
        education_requirements=["Bachelor's degree in Computer Science"],
    )


@pytest.fixture
def strong_matches() -> MatchingResult:
    return MatchingResult(
        matches=[
            SkillMatch(skill="Python", status=MatchStatus.MATCH, confidence=0.95,
                       evidence=[Evidence(text="Python", section="Skills")]),
            SkillMatch(skill="TensorFlow", status=MatchStatus.MATCH, confidence=0.90,
                       evidence=[Evidence(text="TensorFlow", section="Skills")]),
            SkillMatch(skill="AWS", status=MatchStatus.MATCH, confidence=0.92,
                       evidence=[Evidence(text="AWS EC2 and S3", section="Experience")]),
            SkillMatch(skill="SQL", status=MatchStatus.MATCH, confidence=0.88,
                       evidence=[Evidence(text="SQL", section="Skills")]),
            SkillMatch(skill="Machine Learning", status=MatchStatus.MATCH, confidence=0.94,
                       evidence=[Evidence(text="ML Engineer", section="Experience")]),
            SkillMatch(skill="Kubernetes", status=MatchStatus.MATCH, confidence=0.85,
                       evidence=[Evidence(text="Kubernetes", section="Skills")]),
            SkillMatch(skill="Docker", status=MatchStatus.MATCH, confidence=0.85,
                       evidence=[Evidence(text="Docker", section="Skills")]),
            SkillMatch(skill="NLP", status=MatchStatus.MATCH, confidence=0.80,
                       evidence=[Evidence(text="NLP pipelines", section="Experience")]),
        ]
    )


@pytest.fixture
def partial_matches() -> MatchingResult:
    return MatchingResult(
        matches=[
            SkillMatch(skill="Python", status=MatchStatus.MATCH, confidence=0.90),
            SkillMatch(skill="TensorFlow", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
            SkillMatch(skill="AWS", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
            SkillMatch(skill="SQL", status=MatchStatus.MATCH, confidence=0.85),
            SkillMatch(skill="Machine Learning", status=MatchStatus.PARTIAL_MATCH, confidence=0.4),
            SkillMatch(skill="Kubernetes", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
            SkillMatch(skill="Docker", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
            SkillMatch(skill="NLP", status=MatchStatus.NO_EVIDENCE, confidence=0.0),
        ]
    )


@pytest.fixture
def empty_gap_analysis() -> GapAnalysis:
    return GapAnalysis(gaps=[], partial_matches=[], weak_areas=[])


@pytest.fixture
def partial_gap_analysis() -> GapAnalysis:
    return GapAnalysis(
        gaps=[
            Gap(requirement="TensorFlow", status="MISSING", severity=GapSeverity.HIGH,
                reason="No evidence of TensorFlow found in the resume."),
            Gap(requirement="AWS", status="MISSING", severity=GapSeverity.HIGH,
                reason="No evidence of AWS found in the resume."),
        ],
        partial_matches=[
            Gap(requirement="Machine Learning", status="PARTIAL", severity=GapSeverity.MEDIUM,
                reason="Some related experience but no direct ML role."),
        ],
        weak_areas=[],
    )
