"""
GitHub Verification Module
==========================

Independent module for verifying candidate resume claims against
public GitHub evidence.  All extraction is deterministic — no LLM
calls.  Output is structured for downstream consumption by FastAPI
routes, LangGraph tool nodes, or direct PostgreSQL persistence.

Quick start::

    import asyncio
    from github_verifier import verify_candidate

    report = asyncio.run(verify_candidate(
        username="octocat",
        claims=["Built a Python REST API using FastAPI and PostgreSQL"],
    ))

    for c in report.claims:
        print(f"{c.status.value}: {c.claim}  (confidence={c.confidence:.0%})")
"""

from .models import (
    ClaimVerification,
    CommitInfo,
    EvidenceType,
    GitHubProfile,
    Repository,
    TechEvidence,
    VerificationReport,
    VerificationStatus,
)
from .verifier import verify_candidate, verify_candidate_sync, verify_claim
from .client import GitHubClient, validate_username
from .config import GitHubConfig, settings
from .evidence import EvidenceExtractor
from .exceptions import (
    AuthenticationError,
    GitHubAPIError,
    GitHubVerifierError,
    InvalidUsernameError,
    ProfileNotFoundError,
    RateLimitError,
)

__all__ = [
    # Entry points
    "verify_candidate",
    "verify_candidate_sync",
    "verify_claim",
    # Models
    "EvidenceType",
    "VerificationStatus",
    "GitHubProfile",
    "Repository",
    "CommitInfo",
    "TechEvidence",
    "ClaimVerification",
    "VerificationReport",
    # Client & config
    "GitHubClient",
    "GitHubConfig",
    "validate_username",
    "settings",
    # Evidence
    "EvidenceExtractor",
    # Exceptions
    "GitHubVerifierError",
    "GitHubAPIError",
    "RateLimitError",
    "AuthenticationError",
    "ProfileNotFoundError",
    "InvalidUsernameError",
]
