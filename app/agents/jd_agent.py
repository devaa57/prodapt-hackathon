"""
Agent 2 — Job-Description Analyzer

Extracts structured requirements from a raw job description,
including importance weights for each requirement.
"""

from __future__ import annotations

from app.schemas.models import JobAnalysis
from app.services.llm_service import LLMService

SYSTEM_PROMPT = """\
You are an expert job-description analysis agent.

## Objective
Extract structured requirements from the provided job description.

## Rules
1. Extract ONLY requirements **explicitly stated** in the job description.
2. Classify each skill/requirement as **required** (must-have) or **preferred** (nice-to-have).
3. Assign an importance score from 1 to 5 for each requirement:
   - 5 = critical / explicitly marked as mandatory
   - 4 = strongly emphasised
   - 3 = clearly mentioned
   - 2 = mentioned once or implied
   - 1 = nice-to-have / bonus
4. If minimum years of experience is not specified, set minimum_experience_years to 0.
5. Capture education requirements exactly as stated.
6. Put anything that is not a skill, education, or experience requirement into other_requirements.
7. Return your output as valid JSON matching the required schema.

## Hallucination Prevention
- Do NOT add requirements the JD does not mention.
- Do NOT upgrade a preferred skill to required unless the JD clearly says so.
"""


class JDAgent:
    """Analyse a raw job description and return structured JobAnalysis."""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def analyze(self, job_description: str) -> JobAnalysis:
        user_prompt = (
            "Analyse the following job description and extract structured requirements.\n\n"
            "=== JOB DESCRIPTION START ===\n"
            f"{job_description}\n"
            "=== JOB DESCRIPTION END ==="
        )
        return self.llm.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=JobAnalysis,
            temperature=0.1,
        )
