-- Migration 004: Candidate & Resume Tables
-- ============================================================================
-- candidates, resumes, resume_chunks, skills, candidate_skills,
-- experiences, projects

BEGIN;

-- ────────────────────────────────────────────
-- CANDIDATES  — applicants within an org
-- ────────────────────────────────────────────
-- PII is limited to what is strictly necessary for screening.
-- Full PII (address, ID docs) should live in a separate
-- encrypted store if the product goes to production.
CREATE TABLE candidates (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email           VARCHAR(255)    NOT NULL,
    full_name       VARCHAR(255)    NOT NULL,
    phone           VARCHAR(50),
    location        VARCHAR(255),
    source          VARCHAR(100),               -- e.g. 'career_page', 'referral', 'linkedin'
    status          candidate_status NOT NULL DEFAULT 'new',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ,

    CONSTRAINT uq_candidates_org_email UNIQUE (organization_id, email)
);

-- ────────────────────────────────────────────
-- RESUMES  — uploaded resume files + parsed text
-- ────────────────────────────────────────────
CREATE TABLE resumes (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    file_name       VARCHAR(255)    NOT NULL,
    file_url        TEXT,                       -- S3 path or local path
    file_hash       VARCHAR(64),               -- SHA-256 for deduplication
    raw_text        TEXT,                       -- full extracted text
    parsed_data     JSONB,                     -- structured parse output (JSON)
    language        VARCHAR(10)     NOT NULL DEFAULT 'en',
    uploaded_at     TIMESTAMPTZ     NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────
-- RESUME_CHUNKS  — chunked text with embeddings
-- ────────────────────────────────────────────
-- Resume text is split into semantic chunks so that
-- vector similarity search can find the most relevant
-- passage for a given job requirement.
CREATE TABLE resume_chunks (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id       UUID        NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    chunk_index     INTEGER         NOT NULL,
    content         TEXT            NOT NULL,
    section_type    section_type,
    embedding       vector(1536),              -- pgvector column
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uq_resume_chunk_index UNIQUE (resume_id, chunk_index)
);

-- ────────────────────────────────────────────
-- SKILLS  — canonical skills dictionary
-- ────────────────────────────────────────────
-- Shared across all organizations (global lookup).
-- Embedding lets the AI match synonyms (e.g. "React" ↔ "ReactJS").
CREATE TABLE skills (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255)    NOT NULL UNIQUE,
    category        VARCHAR(100),              -- e.g. 'programming_language', 'framework'
    embedding       vector(1536),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────
-- CANDIDATE_SKILLS  — skills attributed to a candidate
-- ────────────────────────────────────────────
CREATE TABLE candidate_skills (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id        UUID        NOT NULL REFERENCES skills(id)     ON DELETE CASCADE,
    proficiency_level proficiency_level,
    years_of_experience NUMERIC(4,1),          -- e.g. 2.5 years
    source          skill_source    NOT NULL DEFAULT 'resume',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uq_candidate_skill UNIQUE (candidate_id, skill_id)
);

-- ────────────────────────────────────────────
-- EXPERIENCES  — work history
-- ────────────────────────────────────────────
CREATE TABLE experiences (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    company_name    VARCHAR(255)    NOT NULL,
    job_title       VARCHAR(255)    NOT NULL,
    location        VARCHAR(255),
    start_date      DATE,
    end_date        DATE,                      -- NULL = current role
    is_current      BOOLEAN         NOT NULL DEFAULT false,
    description     TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT chk_experience_dates CHECK (
        end_date IS NULL OR end_date >= start_date
    )
);

-- ────────────────────────────────────────────
-- PROJECTS  — candidate's notable projects
-- ────────────────────────────────────────────
CREATE TABLE projects (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    title           VARCHAR(255)    NOT NULL,
    description     TEXT,
    url             TEXT,
    technologies    TEXT[],                    -- PostgreSQL array of tech names
    start_date      DATE,
    end_date        DATE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMIT;
