# GitHub Verification Module

Independent, deterministic GitHub verification engine for AI-powered candidate screening. Extracts evidence from public GitHub profiles and repositories to evaluate resume claims without hallucinations or LLM dependencies.

---

## 1. Architecture

```
                               ┌─────────────────────────────┐
                               │       Resume Claims         │
                               │  "Built REST APIs in Go..." │
                               └──────────────┬──────────────┘
                                              ▼
┌──────────────────┐               ┌─────────────────────┐
│  Candidate Input │ ────────────► │   github_verifier   │
│  @username / URL │               │   verify_candidate  │
└──────────────────┘               └──────────┬──────────┘
                                              │
                   ┌──────────────────────────┼──────────────────────────┐
                   ▼                          ▼                          ▼
         ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
         │  profile.py      │       │ repositories.py  │       │   contents.py    │
         │  • Bio, location │       │  • Stars, forks  │       │  • Dependencies  │
         │  • Followers     │       │  • Language mix  │       │  • Dockerfiles   │
         │  • Public repos  │       │  • Topics & desc │       │  • Readme files  │
         └─────────┬────────┘       └─────────┬────────┘       └─────────┬────────┘
                   │                          │                          │
                   └──────────────────────────┼──────────────────────────┘
                                              ▼
                                   ┌─────────────────────┐
                                   │     commits.py      │
                                   │  • Author-filtered  │
                                   │  • Commit messages  │
                                   └──────────┬──────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │     evidence.py     │
                                   │  • Deterministic    │
                                   │  • Confidence weight│
                                   │  • Deduplication    │
                                   └──────────┬──────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │     verifier.py     │
                                   │  • Technology match │
                                   │  • Confidence score │
                                   │  • Status (VERIFIED/│
                                   │    SUPPORTED/INCON) │
                                   └──────────┬──────────┘
                                              │
                   ┌──────────────────────────┴──────────────────────────┐
                   ▼                                                     ▼
     ┌───────────────────────────┐                         ┌───────────────────────────┐
     │   Pydantic Report Object  │                         │    PostgreSQL DB Dict     │
     │   • Structured claims     │                         │    (Matches Migration 006)│
     │   • Extracted evidence    │                         │    • external_profiles    │
     │   • Ready for LangGraph   │                         │    • verification_claims  │
     │     semantic evaluation   │                         │    • verification_evidence│
     └───────────────────────────┘                         └───────────────────────────┘
```

---

## 2. Directory Structure

```
github_verifier/
├── __init__.py          # Public API exports (verify_candidate, GitHubClient, models)
├── client.py            # Async httpx client with rate-limiting, retries, auth
├── commits.py           # Commit extraction with author-filtering
├── config.py            # Environment configuration & defaults via python-dotenv
├── contents.py          # Fetching and parsing package.json, requirements.txt, Dockerfiles, READMEs
├── evidence.py          # Deterministic evidence extractor & confidence scoring
├── exceptions.py        # Custom typed exceptions (RateLimitError, ProfileNotFoundError, etc.)
├── models.py            # Pydantic schemas, ENUMs, and database record serializers
├── profile.py           # User profile fetching & parser
├── repositories.py      # Repository retrieval (filtering forks, pagination, sorting)
├── verifier.py          # End-to-end verification orchestrator & claim evaluation
└── tests/               # 100% offline unit test suite (57 tests)
    ├── __init__.py
    ├── test_client.py   # Username validation & URL normalization tests
    ├── test_evidence.py # Mock dependency/profile/repo/commit extraction tests
    └── test_verifier.py # Technology parsing & confidence algorithm tests
```

---

## 3. Key Design Decisions

1. **Deterministic by Default**: No LLM calls within this module. Claims are matched against technologies identified in dependencies (`package.json`, `requirements.txt`, `go.mod`, `pom.xml`, etc.), languages, topics, commit messages, and READMEs.
2. **Absence of Evidence $\neq$ Contradiction**: If a claimed technology is not found in public repos, it is classified as `INCONCLUSIVE`, never `CONTRADICTED`. `CONTRADICTED` is reserved for explicit opposing signals.
3. **Graceful Degradation & Rate-Limiting**:
   - Inspects `x-ratelimit-remaining` and `x-ratelimit-reset` on every request.
   - Throttles requests when remaining quota is low.
   - Automatically handles 401/403/404 errors with sanitization (tokens are never logged).
4. **Zero-Database Dependency at Runtime**: Produces structured Pydantic models that serialize directly to database dictionaries matching migration schema `006_verification_tables.sql`.

---

## 4. Environment Variables

Create or configure `.env` at the project root:

```ini
# Optional: Personal Access Token (boosts limit from 60 to 5,000 req/hr)
GITHUB_TOKEN=ghp_your_token_here

# Verifier Settings
GITHUB_MAX_REPOS=10
GITHUB_INCLUDE_FORKS=false
GITHUB_PER_PAGE=30
GITHUB_MAX_COMMITS_PER_REPO=20
GITHUB_TIMEOUT_SECONDS=10.0
GITHUB_RATE_LIMIT_MIN_REMAINING=5
```

---

## 5. Verification Status Logic

| Status | Condition | Example |
|---|---|---|
| `VERIFIED` | $\ge 1$ High-confidence evidence source (e.g., direct dependency in manifest, $>500$ lines primary language) AND overall confidence $\ge 0.70$ | Found `express` in `package.json` and Node.js commits |
| `SUPPORTED` | Mentioned in README, topics, bio, or secondary language with confidence $\ge 0.40$ | Found topic `fastapi` or mentioned in README |
| `INCONCLUSIVE` | Confidence $< 0.40$ or technology not detected in public repositories | Candidate claimed Redis, but no Redis usage was found |
| `CONTRADICTED` | Explicit factual conflict | Claimed primary creator of public project owned by someone else |

---

## 6. How LangGraph Agents Call This Module

```python
from github_verifier import verify_candidate

async def verification_node(state: dict) -> dict:
    candidate_github = state.get("github_url")
    claims_to_verify = state.get("resume_claims")

    report = await verify_candidate(
        username=candidate_github,
        claims=claims_to_verify,
    )

    # Pass structured results to downstream evaluation node
    return {
        "verification_report": report.model_dump(mode="json"),
        "db_records": report.to_db_records(candidate_id=state["candidate_id"]),
    }
```

---

## 7. Running Tests & Live Verification

```bash
# Run 57 offline unit tests
python -m pytest github_verifier/tests/ -v

# Run live verification example
python examples/verify_github.py octocat
python examples/verify_github.py torvalds
```
