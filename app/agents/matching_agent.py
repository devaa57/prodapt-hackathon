"""
Agent 3 — Skill Matching

Compares structured resume data against JD requirements,
using RAG-retrieved evidence chunks to justify each classification.
"""

from __future__ import annotations

import json

from app.schemas.models import (
    JobAnalysis,
    MatchingResult,
    ResumeAnalysis,
    RetrievedChunk,
)
from app.services.llm_service import LLMService

SYSTEM_PROMPT = """\
You are a skill-matching specialist agent.

## Objective
Compare a candidate's resume against every requirement in the job description
and classify each requirement.

## Classification Rules
For each requirement, assign ONE of:
- **MATCH**: The resume provides clear, direct evidence the candidate possesses this skill or meets this requirement.
- **PARTIAL_MATCH**: The resume shows related but not exact evidence (e.g. similar technology, adjacent experience).
- **NO_EVIDENCE**: The resume simply does not mention this skill or requirement. This is NOT the same as saying the candidate lacks it.

## Critical Rules
1. NEVER claim a candidate lacks a skill just because it is not mentioned. Use NO_EVIDENCE instead.
2. Provide exact or near-exact quotes from the resume as evidence for MATCH and PARTIAL_MATCH.
3. Assign a confidence score between 0.0 and 1.0 reflecting how strongly the evidence supports the classification.
4. Use ONLY the information provided in the resume and retrieved evidence. Do NOT infer unsupported facts.
5. Evaluate EVERY required and preferred skill from the job description.

## Output
Return a JSON object with a "matches" array. Each element must have:
- skill (string)
- status ("MATCH" | "PARTIAL_MATCH" | "NO_EVIDENCE")
- confidence (float 0.0–1.0)
- evidence (array of objects with "text", "section", "page")
"""


def _format_evidence(evidence_map: dict[str, list[RetrievedChunk]]) -> str:
    """Build a human-readable evidence block for the prompt."""
    lines: list[str] = []
    for skill, chunks in evidence_map.items():
        lines.append(f'\nFor skill "{skill}":')
        if not chunks:
            lines.append("  (no relevant chunks retrieved)")
        for idx, chunk in enumerate(chunks, 1):
            section_info = f", Section: {chunk.section}" if chunk.section else ""
            lines.append(
                f"  [{idx}] (Similarity: {chunk.similarity_score:.2f}{section_info})\n"
                f'  "{chunk.text}"'
            )
    return "\n".join(lines)


class MatchingAgent:
    """Match JD requirements against resume evidence."""

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def match(
        self,
        resume: ResumeAnalysis,
        job: JobAnalysis,
        evidence_map: dict[str, list[RetrievedChunk]],
    ) -> MatchingResult:
        user_prompt = (
            "Compare the candidate's resume against the job requirements.\n\n"
            "=== STRUCTURED RESUME ===\n"
            f"{resume.model_dump_json(indent=2)}\n\n"
            "=== STRUCTURED JOB REQUIREMENTS ===\n"
            f"{job.model_dump_json(indent=2)}\n\n"
            "=== RETRIEVED RESUME EVIDENCE ===\n"
            f"{_format_evidence(evidence_map)}\n\n"
            "Evaluate EVERY required and preferred skill listed above."
        )
        return self.llm.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=MatchingResult,
            temperature=0.1,
        )
