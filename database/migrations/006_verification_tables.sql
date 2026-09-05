-- Migration 006: Verification Tables
-- ============================================================================
-- external_profiles, verification_claims, verification_evidence
--
-- Design note:
--   Verification is SEPARATE from screening.
--   A candidate can score well on screening (resume matches job)
--   but have unverified claims. Conversely, a verified candidate
--   may still be a poor match for a specific job.
--
--   "Not found" → INCONCLUSIVE, never CONTRADICTED.
--   Absence of external evidence does not prove a claim is false.

BEGIN;

-- ────────────────────────────────────────────
-- EXTERNAL_PROFILES  — GitHub, LinkedIn, etc.
-- ────────────────────────────────────────────
CREATE TABLE external_profiles (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID        NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    platform        platform_type   NOT NULL,
    profile_url     TEXT            NOT NULL,
    username        VARCHAR(255),
    profile_data    JSONB,                     -- raw API response data
    last_fetched_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT uq_candidate_platform UNIQUE (candidate_id, platform)
);

-- ────────────────────────────────────────────
-- VERIFICATION_CLAIMS  — what we are trying to verify
-- ────────────────────────────────────────────
CREATE TABLE verification_claims (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    external_profile_id UUID        NOT NULL REFERENCES external_profiles(id) ON DELETE CASCADE,
    claim_type          claim_type          NOT NULL,
    claim_description   TEXT                NOT NULL,
    status              verification_status NOT NULL DEFAULT 'pending',
    confidence_score    NUMERIC(5,2),
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT chk_confidence CHECK (
        confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 100)
    )
);

-- ────────────────────────────────────────────
-- VERIFICATION_EVIDENCE  — proof for/against a claim
-- ────────────────────────────────────────────
CREATE TABLE verification_evidence (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id        UUID        NOT NULL REFERENCES verification_claims(id) ON DELETE CASCADE,
    evidence_type   evidence_source_type NOT NULL,
    evidence_url    TEXT,
    evidence_data   JSONB,                     -- structured evidence payload
    description     TEXT            NOT NULL,
    collected_at    TIMESTAMPTZ     NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

COMMIT;
