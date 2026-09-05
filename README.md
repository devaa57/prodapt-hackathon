# prodapt-hackathon

AI-powered candidate screening and verification platform — developed for the 2026 Prodapt hackathon.

## Overview

The system analyzes job descriptions and resumes, matches candidate skills and experience against job requirements, and provides evidence-backed screening results. It can also verify candidate claims using professional evidence such as GitHub and, where permitted, LinkedIn.

## Project Structure

```
prodapt-hackathon/
├── README.md                      ← this file
└── database/                      ← PostgreSQL database layer
    ├── README.md                  ← database setup guide
    ├── run_migrations.sh          ← migration runner (Linux/macOS)
    ├── run_migrations.bat         ← migration runner (Windows)
    ├── migrations/                ← versioned SQL migration files
    ├── queries/                   ← example SQL queries
    └── diagrams/                  ← ER diagrams (Mermaid)
```

## Getting Started

See [`database/README.md`](database/README.md) for full setup instructions.

### Quick Start (Docker)

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

## Tech Stack

| Component   | Technology                | Cost  |
|------------|---------------------------|-------|
| Database    | PostgreSQL 15+            | Free  |
| Vectors     | pgvector                  | Free  |
| Migrations  | Plain SQL                 | Free  |
| Security    | Row Level Security (RLS)  | Free  |