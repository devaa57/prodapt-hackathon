-- Migration 003: Core Tables — organizations, users, jobs, job_requirements
-- ============================================================================
-- These are the foundational tenant-scoped tables.
-- Every row (except organizations itself) belongs to exactly one organization.

BEGIN;

-- ────────────────────────────────────────────
-- ORGANIZATIONS  — top-level tenant boundary
-- ────────────────────────────────────────────
CREATE TABLE organizations (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255)    NOT NULL,
    slug            VARCHAR(100)    NOT NULL UNIQUE,       -- URL-safe identifier
    domain          VARCHAR(255),                           -- optional corporate domain
    settings        JSONB           NOT NULL DEFAULT '{}',  -- org-level config
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ                             -- soft delete
);

-- ────────────────────────────────────────────
-- USERS  — people who operate the platform
-- ────────────────────────────────────────────
-- Stores only identity + role; password hashes and auth
-- tokens belong in the auth layer (not this schema).
CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email           VARCHAR(255)    NOT NULL,
    full_name       VARCHAR(255)    NOT NULL,
    role            user_role       NOT NULL DEFAULT 'viewer',
    is_active       BOOLEAN         NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ,

    CONSTRAINT uq_users_org_email UNIQUE (organization_id, email)
);

-- ────────────────────────────────────────────
-- JOBS  — open positions within an organization
-- ────────────────────────────────────────────
CREATE TABLE jobs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID                 REFERENCES users(id)   ON DELETE SET NULL,
    title           VARCHAR(255)    NOT NULL,
    description     TEXT,
    department      VARCHAR(255),
    location        VARCHAR(255),
    employment_type employment_type,
    status          job_status      NOT NULL DEFAULT 'draft',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);

-- ────────────────────────────────────────────
-- JOB_REQUIREMENTS  — what a job demands
-- ────────────────────────────────────────────
-- Each requirement can carry an embedding so the AI agent
-- can do vector similarity matching against resume chunks.
--
-- Embedding dimension: 1536 (OpenAI text-embedding-3-small default).
-- If you use a smaller model or MRL truncation, change to 512.
CREATE TABLE job_requirements (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID        NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    requirement_type requirement_type NOT NULL,
    description     TEXT            NOT NULL,
    is_mandatory    BOOLEAN         NOT NULL DEFAULT false,
    min_years       INTEGER,                                -- only for experience reqs
    embedding       vector(1536),                           -- pgvector column
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMIT;
