"""
Pydantic models for the GitHub Verification module.

Every data structure that crosses a module boundary is defined here so
that evidence extraction, claim verification, and downstream consumers
(FastAPI, LangGraph, PostgreSQL persistence) share a single source of truth.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════

class EvidenceType(str, enum.Enum):
    """Where a piece of evidence came from."""
    PROFILE = "PROFILE"
    README = "README"
    DEPENDENCY = "DEPENDENCY"
    LANGUAGE = "LANGUAGE"
    SOURCE_CODE = "SOURCE_CODE"
    COMMIT = "COMMIT"
    TOPIC = "TOPIC"
    REPOSITORY_METADATA = "REPOSITORY_METADATA"


class VerificationStatus(str, enum.Enum):
    """
    Outcome of verifying a claim.

    IMPORTANT: INCONCLUSIVE is the default when evidence is absent.
    Absence of public evidence does NOT equal CONTRADICTED.
    """
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CONTRADICTED = "CONTRADICTED"


# ═══════════════════════════════════════════════════════════════
# Evidence-type confidence weights
# ═══════════════════════════════════════════════════════════════
# Ordered from strongest to weakest.  Used as the *base* confidence
# when a piece of evidence is created.

EVIDENCE_WEIGHTS: dict[EvidenceType, float] = {
    EvidenceType.SOURCE_CODE: 0.95,
    EvidenceType.DEPENDENCY: 0.90,
    EvidenceType.LANGUAGE: 0.75,
    EvidenceType.COMMIT: 0.70,
    EvidenceType.README: 0.60,
    EvidenceType.TOPIC: 0.50,
    EvidenceType.REPOSITORY_METADATA: 0.40,
    EvidenceType.PROFILE: 0.30,
}


# ═══════════════════════════════════════════════════════════════
# GitHub data models
# ═══════════════════════════════════════════════════════════════

class GitHubProfile(BaseModel):
    username: str
    name: str | None = None
    bio: str | None = None
    company: str | None = None
    location: str | None = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    created_at: datetime
    profile_url: str
    avatar_url: str | None = None


class Repository(BaseModel):
    name: str
    full_name: str
    description: str | None = None
    url: str
    html_url: str
    owner: str
    primary_language: str | None = None
    topics: list[str] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None = None
    default_branch: str = "main"
    is_fork: bool = False
    is_archived: bool = False
    size_kb: int = 0


class FileContent(BaseModel):
    path: str
    name: str
    content: str
    size: int
    download_url: str | None = None
    repository: str


class CommitInfo(BaseModel):
    sha: str
    author_name: str | None = None
    author_email: str | None = None
    author_login: str | None = None
    date: datetime
    message: str
    repository: str


# ═══════════════════════════════════════════════════════════════
# Evidence & verification models
# ═══════════════════════════════════════════════════════════════

class TechEvidence(BaseModel):
    """One piece of technology evidence extracted from GitHub."""
    technology: str
    evidence_type: EvidenceType
    source: str                           # e.g. "package.json", "README.md"
    source_url: str
    details: str                          # human-readable explanation
    confidence: float = Field(ge=0.0, le=1.0)
    repository: str | None = None


class ClaimVerification(BaseModel):
    """Result of verifying a single resume claim."""
    claim: str
    status: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    technologies_searched: list[str] = Field(default_factory=list)
    technologies_found: list[str] = Field(default_factory=list)
    technologies_not_found: list[str] = Field(default_factory=list)
    evidence: list[TechEvidence] = Field(default_factory=list)
    reasoning: str = ""


class VerificationReport(BaseModel):
    """Complete verification report for one GitHub profile."""
    username: str
    profile: GitHubProfile
    repositories_analyzed: int = 0
    total_evidence_items: int = 0
    claims: list[ClaimVerification] = Field(default_factory=list)
    all_evidence: list[TechEvidence] = Field(default_factory=list)
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    api_calls_made: int = 0
    errors: list[str] = Field(default_factory=list)

    # ── PostgreSQL mapping helper ──────────────────────────────
    def to_db_records(self, candidate_id: str) -> dict[str, Any]:
        """
        Convert this report into dicts that map directly to the
        PostgreSQL tables: external_profiles, verification_claims,
        verification_evidence.
        """
        profile_record = {
            "candidate_id": candidate_id,
            "platform": "github",
            "profile_url": self.profile.profile_url,
            "username": self.username,
            "profile_data": self.profile.model_dump(mode="json"),
            "last_fetched_at": self.collected_at.isoformat(),
        }

        claim_records: list[dict] = []
        evidence_records: list[dict] = []

        for claim in self.claims:
            claim_record = {
                "claim_type": "skill",
                "claim_description": claim.claim,
                "status": claim.status.value.lower(),
                "confidence_score": round(claim.confidence * 100, 2),
            }
            claim_records.append(claim_record)

            for ev in claim.evidence:
                evidence_records.append(
                    {
                        "evidence_type": _map_evidence_type(ev.evidence_type),
                        "evidence_url": ev.source_url,
                        "description": ev.details,
                        "evidence_data": {
                            "technology": ev.technology,
                            "source": ev.source,
                            "confidence": ev.confidence,
                            "repository": ev.repository,
                        },
                    }
                )

        return {
            "external_profile": profile_record,
            "verification_claims": claim_records,
            "verification_evidence": evidence_records,
        }


def _map_evidence_type(et: EvidenceType) -> str:
    """Map EvidenceType to the PostgreSQL evidence_source_type enum."""
    mapping = {
        EvidenceType.SOURCE_CODE: "code_sample",
        EvidenceType.DEPENDENCY: "github_repo",
        EvidenceType.README: "github_repo",
        EvidenceType.LANGUAGE: "github_repo",
        EvidenceType.COMMIT: "github_commit",
        EvidenceType.TOPIC: "github_repo",
        EvidenceType.REPOSITORY_METADATA: "github_repo",
        EvidenceType.PROFILE: "other",
    }
    return mapping.get(et, "other")
