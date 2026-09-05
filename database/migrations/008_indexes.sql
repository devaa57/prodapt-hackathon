-- Migration 008: Indexes
-- ============================================================================
-- Strategy:
--   1. Foreign-key columns  — PostgreSQL does NOT auto-index FK columns;
--      every FK used in JOINs or filters gets an explicit index.
--   2. Composite indexes    — for the most common multi-column lookups.
--   3. Partial indexes      — for filtering on status/active rows.
--   4. Vector indexes       — HNSW indexes for pgvector similarity search.
--   5. Sorting indexes      — for ORDER BY on scores/timestamps.

BEGIN;

-- ═══════════════════════════════════════════
-- 1. FOREIGN-KEY & LOOKUP INDEXES
-- ═══════════════════════════════════════════

-- organizations
CREATE INDEX idx_organizations_slug        ON organizations (slug);
CREATE INDEX idx_organizations_deleted_at  ON organizations (deleted_at) WHERE deleted_at IS NULL;

-- users
CREATE INDEX idx_users_org_id              ON users (organization_id);
CREATE INDEX idx_users_email               ON users (email);
CREATE INDEX idx_users_active              ON users (organization_id, is_active) WHERE is_active = true AND deleted_at IS NULL;

-- jobs
CREATE INDEX idx_jobs_org_id               ON jobs (organization_id);
CREATE INDEX idx_jobs_created_by           ON jobs (created_by);
CREATE INDEX idx_jobs_status               ON jobs (organization_id, status);
CREATE INDEX idx_jobs_open                 ON jobs (organization_id) WHERE status = 'open' AND deleted_at IS NULL;

-- job_requirements
CREATE INDEX idx_jobreqs_job_id            ON job_requirements (job_id);

-- candidates
CREATE INDEX idx_candidates_org_id         ON candidates (organization_id);
CREATE INDEX idx_candidates_status         ON candidates (organization_id, status);
CREATE INDEX idx_candidates_email          ON candidates (email);
CREATE INDEX idx_candidates_active         ON candidates (organization_id) WHERE deleted_at IS NULL;

-- resumes
CREATE INDEX idx_resumes_candidate_id      ON resumes (candidate_id);
CREATE INDEX idx_resumes_file_hash         ON resumes (file_hash) WHERE file_hash IS NOT NULL;

-- resume_chunks
CREATE INDEX idx_chunks_resume_id          ON resume_chunks (resume_id);

-- skills
CREATE INDEX idx_skills_category           ON skills (category);

-- candidate_skills
CREATE INDEX idx_cskills_candidate_id      ON candidate_skills (candidate_id);
CREATE INDEX idx_cskills_skill_id          ON candidate_skills (skill_id);

-- experiences
CREATE INDEX idx_experiences_candidate_id  ON experiences (candidate_id);

-- projects
CREATE INDEX idx_projects_candidate_id     ON projects (candidate_id);

-- ═══════════════════════════════════════════
-- 2. SCREENING INDEXES
-- ═══════════════════════════════════════════

-- screening_results: fast lookup by job, candidate, or score-sorted
CREATE INDEX idx_screening_job_id          ON screening_results (job_id);
CREATE INDEX idx_screening_candidate_id    ON screening_results (candidate_id);
CREATE INDEX idx_screening_job_score       ON screening_results (job_id, overall_score DESC NULLS LAST);

-- skill_matches
CREATE INDEX idx_skillmatch_screening      ON skill_matches (screening_result_id);
CREATE INDEX idx_skillmatch_skill          ON skill_matches (skill_id);

-- evidence_items
CREATE INDEX idx_evidence_screening        ON evidence_items (screening_result_id);
CREATE INDEX idx_evidence_confidence       ON evidence_items (confidence);

-- gap_analysis
CREATE INDEX idx_gap_screening             ON gap_analysis (screening_result_id);
CREATE INDEX idx_gap_requirement           ON gap_analysis (job_requirement_id);

-- ═══════════════════════════════════════════
-- 3. VERIFICATION INDEXES
-- ═══════════════════════════════════════════

CREATE INDEX idx_extprofiles_candidate_id  ON external_profiles (candidate_id);
CREATE INDEX idx_vclaims_profile_id        ON verification_claims (external_profile_id);
CREATE INDEX idx_vclaims_status            ON verification_claims (status);
CREATE INDEX idx_vevidence_claim_id        ON verification_evidence (claim_id);

-- ═══════════════════════════════════════════
-- 4. AUDIT LOG INDEXES
-- ═══════════════════════════════════════════

CREATE INDEX idx_audit_org_id              ON audit_logs (organization_id);
CREATE INDEX idx_audit_user_id             ON audit_logs (user_id);
CREATE INDEX idx_audit_entity              ON audit_logs (entity_type, entity_id);
CREATE INDEX idx_audit_created_at          ON audit_logs (created_at DESC);
CREATE INDEX idx_audit_action              ON audit_logs (action);

-- ═══════════════════════════════════════════
-- 5. VECTOR INDEXES  (HNSW — best for recall + speed)
-- ═══════════════════════════════════════════
-- HNSW indexes are built at INSERT time and support fast approximate
-- nearest-neighbour search.  Cosine distance (<=>) is standard for
-- normalized text embeddings.
--
-- m  = max connections per node (higher = better recall, more memory)
-- ef_construction = search width during build (higher = better recall)

CREATE INDEX idx_resume_chunks_embedding ON resume_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_jobreqs_embedding ON job_requirements
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_skills_embedding ON skills
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMIT;
