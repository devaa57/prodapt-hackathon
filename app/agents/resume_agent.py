"""
Agent 1 — Resume Analyzer

Extracts structured candidate information from raw resume text.
Only reports what is **explicitly stated**; never infers missing data.
"""

from __future__ import annotations

from app.schemas.models import ResumeAnalysis
from app.services.llm_service import LLMService

SYSTEM_PROMPT = """\
You are an expert resume-analysis agent.

## Objective
Extract structured information from the provided resume text.

## Rules
1. Extract ONLY information **explicitly stated** in the resume.
2. Do NOT infer, assume, or fabricate any information that is not present.
3. If a field has no supporting text, leave it as an empty string, empty list, or zero.
4. For skills, separate technical skills (languages, tools, frameworks) from soft skills (leadership, communication).
5. List every skill once under "skills" and also categorise it under "technical_skills" or "soft_skills".
6. For experience entries, extract role, company, duration in years, and skills used in that role.
7. Calculate total_years_of_experience as the sum of individual experience durations. If dates overlap, estimate conservatively.
8. For education, preserve the exact wording from the resume.
9. Return your output as valid JSON matching the required schema.

## Hallucination Prevention
- You must NOT add skills the candidate did not mention.
- You must NOT embellish job titles or responsibilities.
- If something is ambiguous, prefer the conservative interpretation.
"""


class ResumeAgent:
    """Analyse raw resume text and return structured ResumeAnalysis."""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def analyze(self, resume_text: str) -> ResumeAnalysis:
        user_prompt = (
            "Analyse the following resume and extract structured information.\n\n"
            "=== RESUME START ===\n"
            f"{resume_text}\n"
            "=== RESUME END ==="
        )
        return self.llm.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=ResumeAnalysis,
            temperature=0.1,
        )
