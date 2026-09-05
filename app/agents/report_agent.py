"""
Agent 5 — Report Generator

Produces a recruiter-friendly final report from all prior analyses.
"""

from __future__ import annotations

from app.schemas.models import (
    CandidateReport,
    CandidateScore,
    GapAnalysis,
    JobAnalysis,
    MatchingResult,
    ResumeAnalysis,
)
from app.services.llm_service import LLMService

SYSTEM_PROMPT = """\
You are a professional recruitment-report specialist.

## Objective
Generate a clear, fair, recruiter-friendly screening report.

## Inputs
You receive:
- Structured resume analysis
- Structured job requirements
- Skill-match results
- Gap analysis
- Deterministic candidate score

## Report Guidelines
1. **recommendation**: One of "Strong candidate", "Moderate fit", "Weak fit", or "Not recommended".
   Base this on the total_score:
   - ≥ 75  → "Strong candidate"
   - 50–74 → "Moderate fit"
   - 30–49 → "Weak fit"
   - < 30  → "Not recommended"

2. **summary**: A concise 2-4 sentence evaluation narrative.

3. **strengths**: Key areas where the candidate excels (backed by match evidence).

4. **gaps**: Key areas of concern (use fair language — "No evidence of X" not "Lacks X").

5. **interview_focus**: Specific topics the interviewer should probe based on gaps.

## Critical Rules
- Do NOT invent information not present in the analysis.
- Do NOT contradict the deterministic score.
- Use objective, professional language.
- Be fair: highlight both strengths and areas for exploration.
"""


class ReportAgent:
    """Generate the final recruiter report."""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def generate(
        self,
        resume: ResumeAnalysis,
        job: JobAnalysis,
        matches: MatchingResult,
        gaps: GapAnalysis,
        score: CandidateScore,
    ) -> CandidateReport:
        user_prompt = (
            "Generate a recruiter-friendly screening report.\n\n"
            "=== RESUME ANALYSIS ===\n"
            f"{resume.model_dump_json(indent=2)}\n\n"
            "=== JOB REQUIREMENTS ===\n"
            f"{job.model_dump_json(indent=2)}\n\n"
            "=== SKILL MATCHES ===\n"
            f"{matches.model_dump_json(indent=2)}\n\n"
            "=== GAP ANALYSIS ===\n"
            f"{gaps.model_dump_json(indent=2)}\n\n"
            "=== CANDIDATE SCORE ===\n"
            f"{score.model_dump_json(indent=2)}\n\n"
            "Based on all the above, generate the final report."
        )
        return self.llm.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=CandidateReport,
            temperature=0.3,
        )
