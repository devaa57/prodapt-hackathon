"""
Claim verification engine.

Takes structured evidence (from evidence.py) and resume claims,
then determines verification status with transparent confidence scoring.

Status rules:
  VERIFIED      — confidence ≥ 0.85 AND at least one DEPENDENCY / SOURCE_CODE
  SUPPORTED     — confidence ≥ 0.50
  INCONCLUSIVE  — confidence < 0.50 or no evidence at all
  CONTRADICTED  — only with explicit counter-evidence (extremely rare from
                  GitHub data alone)

Confidence formula (1 − ∏(1 − cᵢ)):
  Naturally caps at 1.0; gives diminishing returns for redundant evidence.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from functools import reduce

from .client import GitHubClient, parse_github_target, validate_username
from .commits import fetch_commits
from .config import GitHubConfig, settings
from .contents import fetch_evidence_files
from .evidence import EvidenceExtractor, TECH_KEYWORDS
from .models import (
    ClaimVerification,
    EvidenceType,
    Repository,
    TechEvidence,
    VerificationReport,
    VerificationStatus,
)
from .profile import fetch_profile
from .repositories import fetch_languages, fetch_repositories

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Technology extraction from claim text
# ═══════════════════════════════════════════════════════════════

def extract_technologies_from_claim(claim: str) -> list[str]:
    """
    Deterministically pull technology names out of a natural-language claim.

    Uses TECH_KEYWORDS for matching.  Short keywords (≤3 chars) use
    word-boundary regex to avoid false positives.
    """
    claim_lower = claim.lower()
    found: list[str] = []

    for tech, keywords in TECH_KEYWORDS.items():
        for kw in keywords:
            if len(kw) <= 3:
                if re.search(r"\b" + re.escape(kw) + r"\b", claim_lower):
                    found.append(tech)
                    break
            else:
                if kw in claim_lower:
                    found.append(tech)
                    break

    return found


# ═══════════════════════════════════════════════════════════════
# Confidence & status computation
# ═══════════════════════════════════════════════════════════════

def calculate_confidence(evidence: list[TechEvidence]) -> float:
    """
    Combine multiple evidence items into one confidence score.

    Formula: 1 − ∏(1 − cᵢ)
    """
    if not evidence:
        return 0.0
    complements = [1.0 - e.confidence for e in evidence]
    combined = 1.0 - reduce(lambda a, b: a * b, complements)
    return round(min(combined, 1.0), 4)


def determine_status(
    confidence: float,
    evidence: list[TechEvidence],
    has_strong: bool,
) -> VerificationStatus:
    if not evidence:
        return VerificationStatus.INCONCLUSIVE
    if confidence >= 0.85 and has_strong:
        return VerificationStatus.VERIFIED
    if confidence >= 0.50:
        return VerificationStatus.SUPPORTED
    return VerificationStatus.INCONCLUSIVE


# ═══════════════════════════════════════════════════════════════
# Single-claim verifier
# ═══════════════════════════════════════════════════════════════

def verify_claim(claim: str, all_evidence: list[TechEvidence]) -> ClaimVerification:
    """Match one resume claim against collected evidence."""
    technologies = extract_technologies_from_claim(claim)

    if not technologies:
        return ClaimVerification(
            claim=claim,
            status=VerificationStatus.INCONCLUSIVE,
            confidence=0.0,
            reasoning="No recognisable technologies found in claim text.",
        )

    found_techs: list[str] = []
    not_found_techs: list[str] = []
    relevant_evidence: list[TechEvidence] = []
    per_tech_conf: list[float] = []

    strong_types = {EvidenceType.SOURCE_CODE, EvidenceType.DEPENDENCY}

    for tech in technologies:
        tech_ev = [
            e for e in all_evidence if e.technology.lower() == tech.lower()
        ]
        if tech_ev:
            found_techs.append(tech)
            relevant_evidence.extend(tech_ev)
            per_tech_conf.append(calculate_confidence(tech_ev))
        else:
            not_found_techs.append(tech)
            per_tech_conf.append(0.0)

    overall = round(
        sum(per_tech_conf) / len(per_tech_conf), 4
    ) if per_tech_conf else 0.0

    has_strong = any(e.evidence_type in strong_types for e in relevant_evidence)
    status = determine_status(overall, relevant_evidence, has_strong)

    # Build human-readable reasoning
    parts: list[str] = []
    for tech in found_techs:
        types = sorted({
            e.evidence_type.value
            for e in relevant_evidence
            if e.technology.lower() == tech.lower()
        })
        parts.append(f"{tech}: found via {', '.join(types)}")
    for tech in not_found_techs:
        parts.append(
            f"{tech}: no public evidence (INCONCLUSIVE — may exist in private repos)"
        )

    return ClaimVerification(
        claim=claim,
        status=status,
        confidence=overall,
        technologies_searched=technologies,
        technologies_found=found_techs,
        technologies_not_found=not_found_techs,
        evidence=relevant_evidence,
        reasoning="; ".join(parts),
    )


# ═══════════════════════════════════════════════════════════════
# Full candidate verification pipeline
# ═══════════════════════════════════════════════════════════════

async def verify_candidate(
    username: str,
    claims: list[str],
    config: GitHubConfig | None = None,
) -> VerificationReport:
    """
    End-to-end verification:

      1. Fetch GitHub profile
      2. Fetch repositories (paginated, filtered)
      3. Per repo → languages, evidence files, commits
      4. Extract structured evidence (deterministic)
      5. Verify each claim against evidence
      6. Return VerificationReport

    This function is the primary entry-point for external callers
    (FastAPI routes, LangGraph tool nodes, CLI scripts).
    """
    cfg = config or settings
    username, target_repo = parse_github_target(username)
    errors: list[str] = []

    async with GitHubClient(cfg) as client:
        # 1. Profile
        profile = await fetch_profile(client, username)

        # 2. Repositories
        repos = await fetch_repositories(client, username, cfg)

        # If a specific repository was targeted in the URL, ensure it is first
        if target_repo:
            target_repo_lower = target_repo.lower()
            matched = [r for r in repos if r.name.lower() == target_repo_lower]
            if matched:
                repos = matched + [r for r in repos if r.name.lower() != target_repo_lower]
            else:
                try:
                    direct_data = await client.get(f"/repos/{username}/{target_repo}")
                    if direct_data and isinstance(direct_data, dict):
                        repos.insert(0, Repository.from_api(direct_data))
                except Exception as exc:
                    logger.warning("Could not fetch target repo %s: %s", target_repo, exc)

        # 3+4. Evidence collection
        extractor = EvidenceExtractor()
        extractor.extract_from_profile(profile)

        for repo in repos:
            extractor.extract_from_repository(repo)

            try:
                # Language breakdown
                langs = await fetch_languages(client, repo.full_name)
                if langs:
                    extractor.extract_from_languages(
                        repo.full_name, repo.html_url, langs,
                    )

                # Evidence files
                files = await fetch_evidence_files(client, repo.full_name, cfg)
                for f in files:
                    name_lower = f.name.lower()
                    if name_lower == "readme.md":
                        extractor.extract_from_readme(f)
                    elif name_lower in ("dockerfile",):
                        extractor.extract_from_dockerfile(f)
                    else:
                        extractor.extract_from_dependencies(f)

                # Commits (author-filtered)
                commits = await fetch_commits(
                    client, repo.full_name, author=username, config=cfg,
                )
                if commits:
                    extractor.extract_from_commits(commits, username)

            except Exception as exc:
                msg = f"Error processing {repo.name}: {exc}"
                logger.warning(msg)
                errors.append(msg)

        # Deduplicate
        all_evidence = extractor.deduplicate()

        # 5. Verify claims
        verified_claims = [verify_claim(c, all_evidence) for c in claims]

        # 6. Report
        return VerificationReport(
            username=username,
            profile=profile,
            repositories_analyzed=len(repos),
            total_evidence_items=len(all_evidence),
            claims=verified_claims,
            all_evidence=all_evidence,
            collected_at=datetime.now(timezone.utc),
            api_calls_made=client.api_calls,
            errors=errors,
        )


def verify_candidate_sync(
    username: str,
    claims: list[str],
    config: GitHubConfig | None = None,
) -> VerificationReport:
    """Synchronous wrapper — convenience for scripts and notebooks."""
    return asyncio.run(verify_candidate(username, claims, config))
