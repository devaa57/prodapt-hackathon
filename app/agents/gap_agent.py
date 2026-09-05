"""
Agent 4 — Gap Analyzer

Identifies missing requirements, partial matches, and weak areas
between the candidate and the JD.
"""

from __future__ import annotations

from app.schemas.models import (
    GapAnalysis,
    JobAnalysis,
    MatchingResult,
    ResumeAnalysis,
    RetrievedChunk,
)
from app.services.llm_service import LLMService

SYSTEM_PROMPT = """\
You are a gap-analysis specialist agent.

## Objective
Identify gaps between a candidate's qualifications and the job requirements.
You receive:
- The structured resume analysis
- The structured job requirements
- Skill-match results
- Retrieved resume evidence

## Rules
1. Identify three categories of gaps:
   - **gaps**: Requirements with NO_EVIDENCE in the resume.
   - **partial_matches**: Requirements classified as PARTIAL_MATCH that need attention.
   - **weak_areas**: Requirements where the candidate falls short of the expected level.

2. For each gap, provide:
   - requirement: the JD requirement
   - status: MISSING | PARTIAL | WEAK
   - severity: HIGH (critical must-have) | MEDIUM (important) | LOW (nice-to-have)
   - reason: a fair, evidence-based explanation

3. CRITICAL LANGUAGE RULES:
   - NEVER say "candidate does not know X" or "candidate lacks X".
   - ALWAYS use phrasing like "No evidence of X found in the resume."
   - Absence of evidence is NOT evidence of absence.

4. Severity mapping:
   - HIGH: importance 4-5 required skills with NO_EVIDENCE
   - MEDIUM: importance 2-3 required skills with NO_EVIDENCE, or importance 4-5 with PARTIAL_MATCH
   - LOW: preferred skills with NO_EVIDENCE, or importance 1-2 with PARTIAL_MATCH

5. Use ONLY the provided information. Do NOT infer unsupported facts.
"""


def _format_evidence(evidence_map: dict[str, list[RetrievedChunk]]) -> str:
    lines: list[str] = []
    for skill, chunks in evidence_map.items():
        lines.append(f'\nFor "{skill}":')
        if not chunks:
            lines.append("  (no relevant chunks)")
        for idx, c in enumerate(chunks, 1):
            lines.append(f'  [{idx}] "{c.text}"')
    return "\n".join(lines)


class GapAgent:
    """Analyse gaps between the candidate and the JD."""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def analyze(
        self,
        job: JobAnalysis,
        resume: ResumeAnalysis,
        matches: MatchingResult,
        evidence_map: dict[str, list[RetrievedChunk]],
    ) -> GapAnalysis:
        user_prompt = (
            "Analyse the gaps between this candidate and the job requirements.\n\n"
            "=== STRUCTURED JOB REQUIREMENTS ===\n"
            f"{job.model_dump_json(indent=2)}\n\n"
            "=== STRUCTURED RESUME ===\n"
            f"{resume.model_dump_json(indent=2)}\n\n"
            "=== SKILL MATCH RESULTS ===\n"
            f"{matches.model_dump_json(indent=2)}\n\n"
            "=== RETRIEVED EVIDENCE ===\n"
            f"{_format_evidence(evidence_map)}\n\n"
            "Identify all gaps, partial matches, and weak areas."
        )
        return self.llm.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=GapAnalysis,
            temperature=0.1,
        )
