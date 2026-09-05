# 🗄️ AI Candidate Screening — Database

PostgreSQL database for an AI-powered candidate screening and verification platform.  
Multi-tenant, vector-enabled, evidence-based, and production-oriented.

> **Everything here is 100% free and open-source.**  
> PostgreSQL · pgvector · plain SQL migrations · no paid services.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Schema Summary](#schema-summary)
- [Migration Structure](#migration-structure)
- [pgvector & Embeddings](#pgvector--embeddings)
- [Row Level Security (RLS)](#row-level-security-rls)
- [Audit Log Design](#audit-log-design)
- [Key Design Decisions](#key-design-decisions)
- [Example Queries](#example-queries)
- [Connecting from Application Code](#connecting-from-application-code)
- [Resetting the Database](#resetting-the-database)

---

## Quick Start

### 1. Install PostgreSQL 15+ and pgvector

**Windows (using installer):**
```bash
# Download from https://www.postgresql.org/download/windows/
# After install, add PostgreSQL bin to your PATH
# Then install pgvector:
# Download from https://github.com/pgvector/pgvector/releases
# Copy the DLL + SQL files into your PostgreSQL extension directory
```

**macOS:**
```bash
brew install postgresql@16
brew install pgvector
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-16 postgresql-16-pgvector
```

**Docker (recommended for hackathon):**
```bash
docker run -d \
  --name screening-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=screening_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

The `pgvector/pgvector` Docker image is free and comes with pgvector pre-installed.

### 2. Run Migrations

**Python Runner (Cross-platform - Recommended):**
```bash
# Uses DATABASE_URL from .env automatically
python database/run_migrations.py --seed

# Or check status and list tables:
python database/run_migrations.py --status
```

**Linux / macOS / Git Bash (psql):**
```bash
cd database
chmod +x run_migrations.sh
./run_migrations.sh --seed
```

**Windows (Command Prompt / psql):**
```cmd
cd database
run_migrations.bat --seed
```

**Manual (any OS):**
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE screening_db;"

# Run each migration in order
psql -U postgres -d screening_db -f migrations/001_extensions.sql
psql -U postgres -d screening_db -f migrations/002_types.sql
psql -U postgres -d screening_db -f migrations/003_core_tables.sql
psql -U postgres -d screening_db -f migrations/004_candidate_resume_tables.sql
psql -U postgres -d screening_db -f migrations/005_screening_tables.sql
psql -U postgres -d screening_db -f migrations/006_verification_tables.sql
psql -U postgres -d screening_db -f migrations/007_audit_log.sql
psql -U postgres -d screening_db -f migrations/008_indexes.sql
psql -U postgres -d screening_db -f migrations/009_rls_policies.sql
psql -U postgres -d screening_db -f migrations/010_seed_data.sql   # optional
```

### 3. Verify

```bash
psql -U postgres -d screening_db -c "\dt"
```

You should see 19 tables.

---

## Prerequisites

| Tool         | Version | Free? | Purpose                          |
|-------------|---------|-------|----------------------------------|
| PostgreSQL   | 15+     | ✅ Yes | Relational database              |
| pgvector     | 0.5+    | ✅ Yes | Vector similarity search         |
| psql         | any     | ✅ Yes | CLI for running migrations       |
| Docker       | any     | ✅ Yes | Optional — easiest local setup   |

---

## Architecture Overview

```
organizations
    ├── users
    ├── jobs
    │     └── job_requirements  (+ embeddings)
    └── candidates
          ├── resumes
          │     └── resume_chunks  (+ embeddings)
          ├── candidate_skills
          ├── experiences
          ├── projects
          └── external_profiles
                 └── verification_claims
                        └── verification_evidence

jobs + candidates
        ↓
screening_results
        ├── skill_matches
        ├── evidence_items
        └── gap_analysis

users/actions → audit_logs
```

**Tenant isolation**: Every table chains back to `organizations.id` via foreign keys. Row Level Security (RLS) ensures one organization can never read another's data.

**Vector search**: `resume_chunks`, `job_requirements`, and `skills` carry `vector(1536)` columns for embedding-based similarity matching.

---

## Schema Summary

### Core (4 tables)

| Table              | Purpose                                     | Key Columns                              |
|-------------------|---------------------------------------------|------------------------------------------|
| `organizations`    | Top-level tenant boundary                   | id, name, slug, domain                   |
| `users`            | Platform operators (admins, recruiters)      | id, org_id, email, role                  |
| `jobs`             | Open positions                              | id, org_id, title, status                |
| `job_requirements` | What a job demands (with optional embedding) | id, job_id, type, description, embedding |

### Candidate & Resume (7 tables)

| Table              | Purpose                                   | Key Columns                                  |
|-------------------|-------------------------------------------|----------------------------------------------|
| `candidates`       | Applicants within an org                  | id, org_id, email, full_name, status         |
| `resumes`          | Uploaded resume files + parsed text        | id, candidate_id, file_name, raw_text        |
| `resume_chunks`    | Chunked text with embeddings              | id, resume_id, chunk_index, content, embedding|
| `skills`           | Global canonical skills dictionary        | id, name, category, embedding                |
| `candidate_skills` | Skills attributed to a candidate          | id, candidate_id, skill_id, proficiency      |
| `experiences`      | Work history                              | id, candidate_id, company, title, dates      |
| `projects`         | Notable projects                          | id, candidate_id, title, technologies[]      |

### Screening (4 tables)

| Table              | Purpose                                   | Key Columns                                  |
|-------------------|-------------------------------------------|----------------------------------------------|
| `screening_results`| AI-generated match assessment             | id, job_id, candidate_id, overall_score      |
| `skill_matches`    | Per-skill match detail                    | id, screening_id, match_strength, score      |
| `evidence_items`   | Proof backing a screening decision        | id, screening_id, evidence_type, confidence  |
| `gap_analysis`     | What the candidate is missing             | id, screening_id, gap_type, severity         |

### Verification (3 tables)

| Table                  | Purpose                              | Key Columns                              |
|-----------------------|--------------------------------------|------------------------------------------|
| `external_profiles`    | GitHub, LinkedIn, etc.               | id, candidate_id, platform, profile_url  |
| `verification_claims`  | Claims to be verified                | id, profile_id, claim_type, status       |
| `verification_evidence`| Proof for/against a claim            | id, claim_id, evidence_type, evidence_url|

### Security (1 table)

| Table        | Purpose              | Key Columns                                    |
|-------------|----------------------|------------------------------------------------|
| `audit_logs` | Append-only action log | id, org_id, user_id, action, entity_type, entity_id |

---

## Migration Structure

Migrations are numbered and must be run **in order**:

```
database/migrations/
├── 001_extensions.sql          ← pgvector + pgcrypto
├── 002_types.sql               ← ENUM type definitions
├── 003_core_tables.sql         ← organizations, users, jobs, job_requirements
├── 004_candidate_resume_tables.sql ← candidates, resumes, chunks, skills
├── 005_screening_tables.sql    ← screening_results, matches, evidence, gaps
├── 006_verification_tables.sql ← external_profiles, claims, evidence
├── 007_audit_log.sql           ← audit_logs + append-only triggers
├── 008_indexes.sql             ← all indexes (FK, composite, partial, HNSW)
├── 009_rls_policies.sql        ← Row Level Security policies
└── 010_seed_data.sql           ← sample data (dev/demo only)
```

Each migration is wrapped in `BEGIN; ... COMMIT;` for transactional safety.

---

## pgvector & Embeddings

### Setup

pgvector is enabled in `001_extensions.sql`:
```sql
CREATE EXTENSION IF NOT EXISTS "vector";
```

### Vector Columns

| Table              | Column      | Dimensions | Purpose                                    |
|-------------------|-------------|------------|--------------------------------------------|
| `resume_chunks`    | `embedding` | 1536       | Semantic search over resume text            |
| `job_requirements` | `embedding` | 1536       | Match requirements against resume chunks    |
| `skills`           | `embedding` | 1536       | Find similar/synonymous skills              |

**Why 1536?** This is the native dimension for OpenAI `text-embedding-3-small` (free tier available). If you use a different model or want to reduce storage, change to `512` — OpenAI supports MRL truncation with minimal quality loss.

### Vector Indexes (HNSW)

```sql
CREATE INDEX idx_resume_chunks_embedding ON resume_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**HNSW** (Hierarchical Navigable Small World) provides fast approximate nearest-neighbour search with good recall. The `vector_cosine_ops` operator class uses cosine distance, which is standard for normalized text embeddings.

### Similarity Search Example

```sql
-- Find resume chunks most similar to a job requirement
SELECT
    rc.content,
    rc.embedding <=> jr.embedding AS cosine_distance
FROM resume_chunks rc
CROSS JOIN (
    SELECT embedding FROM job_requirements WHERE id = :req_id
) jr
WHERE rc.embedding IS NOT NULL
ORDER BY cosine_distance ASC
LIMIT 5;
```

---

## Row Level Security (RLS)

### Strategy

The application sets a session variable before executing any query:

```sql
SET app.current_org_id = '<organization-uuid>';
```

A helper function reads this variable:

```sql
CREATE FUNCTION current_org_id() RETURNS UUID ...
```

RLS policies filter every `SELECT`, `INSERT`, `UPDATE`, `DELETE`:

```sql
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_candidates ON candidates
    USING (organization_id = current_org_id());
```

### Tables with RLS

All 17 tenant-scoped tables have RLS policies. Child tables (e.g. `resume_chunks`) chain through JOINs to reach `organization_id`.

### Tables without RLS

- `organizations` — the app needs to read the org row to set `current_org_id`
- `skills` — global lookup shared across all tenants

### Important: Application Role

> **The database connection user must NOT be a superuser** — superusers bypass RLS.  
> Create a dedicated role for the application:
>
> ```sql
> CREATE ROLE app_user LOGIN PASSWORD 'your_password';
> GRANT USAGE ON SCHEMA public TO app_user;
> GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
> GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;
> ```

---

## Audit Log Design

### Principles

1. **Append-only**: A database trigger physically prevents `UPDATE` and `DELETE` on `audit_logs`.
2. **Polymorphic**: `entity_type` + `entity_id` can reference any table.
3. **Change capture**: `old_values` and `new_values` as JSONB capture what changed.
4. **No soft-delete**: Audit records are permanent.

### How to Log from Application Code

```python
# FastAPI example (pseudo-code)
async def create_candidate(candidate_data, current_user):
    candidate = await db.execute(insert_candidate_sql, candidate_data)
    await db.execute("""
        INSERT INTO audit_logs (organization_id, user_id, action, entity_type, entity_id, new_values)
        VALUES ($1, $2, 'create', 'candidate', $3, $4)
    """, current_user.org_id, current_user.id, candidate.id, json.dumps(candidate_data))
```

---

## Key Design Decisions

### 1. Screening ≠ Verification

Screening scores ("does this resume match this job?") and verification results ("is this claim true?") are stored in **completely separate table groups**. A high screening score with unverified claims is a different signal than a low score with verified claims. They must never be conflated.

### 2. "Not found" ≠ "False"

The `confidence_level` ENUM includes `inconclusive`. When external evidence cannot be found (e.g. no public GitHub for a claimed project), the system defaults to `inconclusive`, **not** `contradicted`. A candidate may have private repos, NDA-protected work, or incomplete public presence.

### 3. ENUMs over VARCHAR + CHECK

Using PostgreSQL `ENUM` types instead of `VARCHAR` with `CHECK` constraints provides:
- Type safety at the database level
- Better storage efficiency (4 bytes vs variable-length)
- Richer query planner metadata

### 4. UUID Primary Keys

UUIDs avoid sequential ID exposure, enable distributed ID generation (useful for Celery workers or multiple API instances), and prevent enumeration attacks.

### 5. Soft Delete via `deleted_at`

Core entities (`organizations`, `users`, `jobs`, `candidates`) support soft deletion. This allows data recovery and maintains referential integrity for audit trails. Partial indexes (e.g. `WHERE deleted_at IS NULL`) ensure soft-deleted rows don't slow down active queries.

### 6. JSONB for Flexible Data

`parsed_data`, `profile_data`, `evidence_data`, `settings`, and audit `old_values`/`new_values` use JSONB. This avoids schema rigidity for data that varies by source (different resume parsers, different GitHub API responses, etc.).

---

## Example Queries

See [`queries/example_queries.sql`](queries/example_queries.sql) for 11 ready-to-run queries covering:

1. Find top candidates for a job (by score)
2. Retrieve all skills for a candidate
3. Retrieve resume evidence for a screening result
4. Retrieve verification evidence for a candidate
5. Vector similarity search (resume chunks ↔ job requirements)
6. Find similar skills (vector similarity)
7. Full candidate screening report
8. Candidate work history + projects
9. Gap analysis — what is a candidate missing?
10. Audit log — recent actions
11. Candidates with unverified claims (verification queue)

---

## Connecting from Application Code

### Connection String

```
postgresql://app_user:password@localhost:5432/screening_db
```

### Setting Tenant Context (required for RLS)

Every request handler must set the organization context:

```python
# FastAPI middleware example
@app.middleware("http")
async def set_org_context(request, call_next):
    org_id = get_org_id_from_token(request)  # your auth logic
    await db.execute(f"SET app.current_org_id = '{org_id}'")
    response = await call_next(request)
    return response
```

### Environment Variables

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=screening_db
DB_USER=app_user
DB_PASSWORD=your_password
```

---

## Resetting the Database

```bash
# Drop and recreate
psql -U postgres -c "DROP DATABASE IF EXISTS screening_db;"
psql -U postgres -c "CREATE DATABASE screening_db;"

# Re-run migrations
./run_migrations.sh --seed        # Linux/macOS
run_migrations.bat --seed         # Windows
```

---

## File Structure

```
database/
├── README.md                   ← this file
├── run_migrations.sh           ← migration runner (Linux/macOS)
├── run_migrations.bat          ← migration runner (Windows)
├── migrations/
│   ├── 001_extensions.sql
│   ├── 002_types.sql
│   ├── 003_core_tables.sql
│   ├── 004_candidate_resume_tables.sql
│   ├── 005_screening_tables.sql
│   ├── 006_verification_tables.sql
│   ├── 007_audit_log.sql
│   ├── 008_indexes.sql
│   ├── 009_rls_policies.sql
│   └── 010_seed_data.sql
├── queries/
│   └── example_queries.sql
└── diagrams/
    └── er_diagram.md
```
