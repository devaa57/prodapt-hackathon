# prodapt-hackathon

AI-powered candidate screening and verification platform — developed for the 2026 Prodapt hackathon.

## Overview

The system analyzes job descriptions and resumes, matches candidate skills and experience against job requirements, and provides evidence-backed screening results. It can also verify candidate claims using professional evidence such as GitHub and, where permitted, LinkedIn.

## Project Structure

```
prodapt-hackathon/
├── README.md                      ← this file
├── requirements.txt               ← python dependencies
├── .env.example                   ← sample environment configuration
├── database/                      ← PostgreSQL database layer
│   ├── README.md                  ← database setup guide
│   ├── run_migrations.sh          ← migration runner (Linux/macOS)
│   ├── run_migrations.bat         ← migration runner (Windows)
│   ├── migrations/                ← versioned SQL migration files (001-010)
│   ├── queries/                   ← example SQL queries
│   └── diagrams/                  ← ER diagrams (Mermaid)
├── github_verifier/               ← GitHub verification engine
│   ├── README.md                  ← verifier module documentation
│   ├── client.py                  ← async GitHub REST API client
│   ├── config.py                  ← configuration & settings
│   ├── models.py                  ← Pydantic models & DB serializers
│   ├── profile.py                 ← profile data fetcher
│   ├── repositories.py            ← repo metadata & filtering
│   ├── contents.py                ← manifests & dockerfiles fetcher
│   ├── commits.py                 ← author-filtered commits
│   ├── evidence.py                ← deterministic evidence extraction
│   ├── verifier.py                ← claim verification engine
│   └── tests/                     ← 57 offline unit tests
└── examples/
    └── verify_github.py           ← end-to-end verification CLI runner
```

## Getting Started

### 1. Database Setup

See [`database/README.md`](database/README.md) for full setup instructions.

```bash
# Start PostgreSQL with pgvector
docker run -d --name screening-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=screening_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Run migrations with seed data
cd database
./run_migrations.sh --seed        # Linux/macOS
run_migrations.bat --seed         # Windows
```

### 2. GitHub Verifier Setup

See [`github_verifier/README.md`](github_verifier/README.md) for architecture & API details.

```bash
# Install dependencies
pip install -r requirements.txt

# Run offline unit test suite (57 tests)
python -m pytest github_verifier/tests/ -v

# Run verification example
python examples/verify_github.py octocat
```

## Tech Stack

| Component           | Technology                | Cost  |
|--------------------|---------------------------|-------|
| Database           | PostgreSQL 15+            | Free  |
| Vectors            | pgvector                  | Free  |
| Migrations         | Plain SQL                 | Free  |
| Security           | Row Level Security (RLS)  | Free  |
| GitHub Client      | httpx (async HTTP/2)      | Free  |
| Validation/Schemas | Pydantic v2               | Free  |
| GitHub API         | Official REST API v3      | Free (60/hr unauth, 5000/hr auth) |
| Testing            | pytest + pytest-asyncio   | Free  |
