-- Migration 005: Screening Tables
-- ============================================================================
-- screening_results, skill_matches, evidence_items, gap_analysis
--
-- Design note:
--   Screening scores represent "how well does this candidate match this job?"
--   They are NOT hiring decisions. Verification scores (migration 006) are
--   stored separately and must never be conflated with screening scores.

BEGIN;

-- ────────────────────────────────────────────
-- SCREENING_RESULTS  — AI-generated match assessment
-- ────────────────────────────────────────────
-- One result per (job, candidate) pair.
CREATE TABLE screening_results (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id                  UUID        NOT NULL REFERENCES jobs(id)       ON DELETE CASCADE,
    candidate_id            UUID        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    overall_score           NUMERIC(5,2),          -- 0.00 – 100.00
    skill_match_score       NUMERIC(5,2),
    experience_match_score  NUMERIC(5,2),
    summary                 TEXT,                  -- human-readable explanation
    recommendation          screening_recommendation,
    screened_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    screened_by             VARCHAR(100),          -- 'ai_agent' or user UUID
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_screening_job_candidate UNIQUE (job_id, candidate_id),
    CONSTRAINT chk_overall_score   CHECK (overall_score    IS NULL OR (overall_score    >= 0 AND overall_score    <= 100)),
    CONSTRAINT chk_skill_score     CHECK (skill_match_score IS NULL OR (skill_match_score >= 0 AND skill_match_score <= 100)),
    CONSTRAINT chk_exp_score       CHECK (experience_match_score IS NULL OR (experience_match_score >= 0 AND experience_match_score <= 100))
);

-- ────────────────────────────────────────────
-- SKILL_MATCHES  — per-skill match detail
-- ────────────────────────────────────────────
CREATE TABLE skill_matches (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_result_id     UUID        NOT NULL REFERENCES screening_results(id) ON DELETE CASCADE,
    skill_id                UUID                 REFERENCES skills(id)             ON DELETE SET NULL,
    job_requirement_id      UUID                 REFERENCES job_requirements(id)   ON DELETE SET NULL,
    candidate_skill_id      UUID                 REFERENCES candidate_skills(id)   ON DELETE SET NULL,
    match_strength          match_strength NOT NULL,
    score                   NUMERIC(5,2),
    explanation             TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_match_score CHECK (score IS NULL OR (score >= 0 AND score <= 100))
);

-- ────────────────────────────────────────────
-- EVIDENCE_ITEMS  — proof backing a screening decision
-- ────────────────────────────────────────────
-- Each piece of evidence has a confidence level:
--   verified     – independently confirmed
--   supported    – consistent with available data
--   inconclusive – not enough information (default for missing data)
--   contradicted – conflicts with other evidence
CREATE TABLE evidence_items (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_result_id     UUID        NOT NULL REFERENCES screening_results(id) ON DELETE CASCADE,
    evidence_type           evidence_item_type NOT NULL,
    content                 TEXT            NOT NULL,
    source_reference        TEXT,                  -- URL or internal ref
    confidence              confidence_level NOT NULL DEFAULT 'inconclusive',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ────────────────────────────────────────────
-- GAP_ANALYSIS  — what the candidate is missing
-- ────────────────────────────────────────────
CREATE TABLE gap_analysis (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    screening_result_id     UUID        NOT NULL REFERENCES screening_results(id)   ON DELETE CASCADE,
    job_requirement_id      UUID        NOT NULL REFERENCES job_requirements(id)     ON DELETE CASCADE,
    gap_type                gap_type        NOT NULL,
    severity                gap_severity    NOT NULL,
    description             TEXT            NOT NULL,
    suggestion              TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
