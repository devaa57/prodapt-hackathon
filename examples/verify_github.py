#!/usr/bin/env python3
"""
Example: Verify a GitHub profile against resume claims.

Usage:
    python examples/verify_github.py                        # uses "octocat"
    python examples/verify_github.py torvalds               # any public user
    python examples/verify_github.py https://github.com/user

Requirements:
    pip install -r requirements.txt
    Optionally set GITHUB_TOKEN in .env for higher rate limits.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

# Ensure UTF-8 output across Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on sys.path for standalone execution
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from github_verifier import verify_candidate


DEFAULT_CLAIMS = [
    "Built an e-commerce backend using Node.js, Express, PostgreSQL and Redis.",
    "Experienced in Python and machine learning with TensorFlow.",
    "Deployed microservices using Docker and Kubernetes.",
    "Developed REST APIs using Django and PostgreSQL.",
    "Built a React frontend with TypeScript.",
]


async def main(username: str, claims: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  GitHub Verification — @{username}")
    print(f"{'='*60}\n")

    report = await verify_candidate(username=username, claims=claims)

    # ── Profile summary ──
    p = report.profile
    print(f"Profile:  {p.name or p.username}")
    print(f"Bio:      {p.bio or '(none)'}")
    print(f"Location: {p.location or '(none)'}")
    print(f"Repos:    {p.public_repos}  |  Followers: {p.followers}")
    print(f"Joined:   {p.created_at:%Y-%m-%d}")
    print(f"\nRepos analysed:   {report.repositories_analyzed}")
    print(f"Evidence items:   {report.total_evidence_items}")
    print(f"API calls made:   {report.api_calls_made}")

    if report.errors:
        print(f"\n⚠ Errors:  {len(report.errors)}")
        for e in report.errors:
            print(f"  - {e}")

    # ── Claim results ──
    print(f"\n{'─'*60}")
    print("CLAIM VERIFICATION RESULTS")
    print(f"{'─'*60}")

    for i, c in enumerate(report.claims, 1):
        status_icon = {
            "VERIFIED": "✅", "SUPPORTED": "🟡",
            "INCONCLUSIVE": "❓", "CONTRADICTED": "❌",
        }.get(c.status.value, "?")

        print(f"\n{i}. {c.claim}")
        print(f"   Status:     {status_icon} {c.status.value}")
        print(f"   Confidence: {c.confidence:.0%}")
        if c.technologies_found:
            print(f"   Found:      {', '.join(c.technologies_found)}")
        if c.technologies_not_found:
            print(f"   Not found:  {', '.join(c.technologies_not_found)}")
        print(f"   Reasoning:  {c.reasoning}")

        if c.evidence:
            print(f"   Evidence ({len(c.evidence)} items):")
            for ev in c.evidence[:5]:  # Show top 5
                print(f"     • [{ev.evidence_type.value}] {ev.technology}: {ev.details}")

    # ── JSON output ──
    print(f"\n{'─'*60}")
    print("JSON OUTPUT (first claim)")
    print(f"{'─'*60}")
    if report.claims:
        print(json.dumps(report.claims[0].model_dump(mode="json"), indent=2))

    # ── DB mapping ──
    print(f"\n{'─'*60}")
    print("DATABASE MAPPING (to_db_records)")
    print(f"{'─'*60}")
    db = report.to_db_records(candidate_id="e0000000-0000-0000-0000-000000000001")
    print(json.dumps(db["external_profile"], indent=2, default=str))
    print(f"\nClaims:   {len(db['verification_claims'])} records")
    print(f"Evidence: {len(db['verification_evidence'])} records")


from datetime import datetime, timezone
from github_verifier.exceptions import (
    GitHubVerifierError,
    InvalidUsernameError,
    ProfileNotFoundError,
    RateLimitError,
)

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "octocat"
    try:
        asyncio.run(main(username, DEFAULT_CLAIMS))
    except RateLimitError as exc:
        reset_time = ""
        if exc.reset_at:
            dt = datetime.fromtimestamp(exc.reset_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            reset_time = f" (resets at {dt})"
        print(f"\n❌ GitHub API Rate Limit Exceeded{reset_time}.")
        print("💡 Tip: Set GITHUB_TOKEN in .env (or environment) for 5,000 requests/hour.")
        print("   Generate a free personal access token at: https://github.com/settings/tokens")
        sys.exit(1)
    except ProfileNotFoundError as exc:
        print(f"\n❌ GitHub profile not found: {exc.username}")
        sys.exit(1)
    except InvalidUsernameError as exc:
        print(f"\n❌ Invalid GitHub username: {exc}")
        sys.exit(1)
    except GitHubVerifierError as exc:
        print(f"\n❌ GitHub Verifier Error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ Unexpected error: {exc}")
        sys.exit(1)
