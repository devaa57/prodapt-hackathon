-- Migration 009: Row Level Security (RLS) Policies
-- ============================================================================
--
-- Strategy:
--   The application layer (FastAPI / connection pool) sets a session variable
--   BEFORE executing any query:
--
--       SET app.current_org_id = '<organization-uuid>';
--
--   RLS policies then transparently filter every SELECT/INSERT/UPDATE/DELETE
--   so that a tenant can never see another tenant's data.
--
--   This means:
--     • The DB connection user must NOT be a superuser (superusers bypass RLS).
--     • Use a dedicated 'app_user' role for the application.
--
-- Tables covered:
--   users, jobs, job_requirements, candidates, resumes, resume_chunks,
--   candidate_skills, experiences, projects, screening_results,
--   external_profiles, verification_claims, verification_evidence,
--   audit_logs
--
-- Tables NOT covered:
--   organizations — a user should only see their own org, but the app
--                    typically fetches the org row to set current_org_id,
--                    so we leave it unprotected or add a separate policy.
--   skills — global lookup table shared across all tenants.

BEGIN;

-- ─────────────────────────────────────────────────────────
-- Helper function: returns the current tenant UUID
-- ─────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION current_org_id()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_org_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- ─────────────────────────────────────────────────────────
-- MACRO: Enable RLS + create tenant isolation policy
-- (Applied per table below)
-- ─────────────────────────────────────────────────────────

-- ── users ──
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_users ON users
    USING (organization_id = current_org_id());

-- ── jobs ──
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_jobs ON jobs
    USING (organization_id = current_org_id());

-- ── candidates ──
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_candidates ON candidates
    USING (organization_id = current_org_id());

-- ── job_requirements (via join to jobs) ──
ALTER TABLE job_requirements ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_jobreqs ON job_requirements
    USING (
        EXISTS (
            SELECT 1 FROM jobs
            WHERE jobs.id = job_requirements.job_id
              AND jobs.organization_id = current_org_id()
        )
    );

-- ── resumes (via join to candidates) ──
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_resumes ON resumes
    USING (
        EXISTS (
            SELECT 1 FROM candidates
            WHERE candidates.id = resumes.candidate_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── resume_chunks (via join to resumes → candidates) ──
ALTER TABLE resume_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_chunks ON resume_chunks
    USING (
        EXISTS (
            SELECT 1 FROM resumes
            JOIN candidates ON candidates.id = resumes.candidate_id
            WHERE resumes.id = resume_chunks.resume_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── candidate_skills (via join to candidates) ──
ALTER TABLE candidate_skills ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_cskills ON candidate_skills
    USING (
        EXISTS (
            SELECT 1 FROM candidates
            WHERE candidates.id = candidate_skills.candidate_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── experiences (via join to candidates) ──
ALTER TABLE experiences ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_experiences ON experiences
    USING (
        EXISTS (
            SELECT 1 FROM candidates
            WHERE candidates.id = experiences.candidate_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── projects (via join to candidates) ──
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_projects ON projects
    USING (
        EXISTS (
            SELECT 1 FROM candidates
            WHERE candidates.id = projects.candidate_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── screening_results (via join to candidates) ──
ALTER TABLE screening_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_screening ON screening_results
    USING (
        EXISTS (
            SELECT 1 FROM candidates
            WHERE candidates.id = screening_results.candidate_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── skill_matches (via screening_results → candidates) ──
ALTER TABLE skill_matches ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_skillmatches ON skill_matches
    USING (
        EXISTS (
            SELECT 1 FROM screening_results
            JOIN candidates ON candidates.id = screening_results.candidate_id
            WHERE screening_results.id = skill_matches.screening_result_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── evidence_items (via screening_results → candidates) ──
ALTER TABLE evidence_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_evidence ON evidence_items
    USING (
        EXISTS (
            SELECT 1 FROM screening_results
            JOIN candidates ON candidates.id = screening_results.candidate_id
            WHERE screening_results.id = evidence_items.screening_result_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── gap_analysis (via screening_results → candidates) ──
ALTER TABLE gap_analysis ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_gaps ON gap_analysis
    USING (
        EXISTS (
            SELECT 1 FROM screening_results
            JOIN candidates ON candidates.id = gap_analysis.screening_result_id
            WHERE screening_results.id = gap_analysis.screening_result_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── external_profiles (via candidates) ──
ALTER TABLE external_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_extprofiles ON external_profiles
    USING (
        EXISTS (
            SELECT 1 FROM candidates
            WHERE candidates.id = external_profiles.candidate_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── verification_claims (via external_profiles → candidates) ──
ALTER TABLE verification_claims ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_vclaims ON verification_claims
    USING (
        EXISTS (
            SELECT 1 FROM external_profiles
            JOIN candidates ON candidates.id = external_profiles.candidate_id
            WHERE external_profiles.id = verification_claims.external_profile_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── verification_evidence (via verification_claims → external_profiles → candidates) ──
ALTER TABLE verification_evidence ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_vevidence ON verification_evidence
    USING (
        EXISTS (
            SELECT 1 FROM verification_claims
            JOIN external_profiles ON external_profiles.id = verification_claims.external_profile_id
            JOIN candidates ON candidates.id = external_profiles.candidate_id
            WHERE verification_claims.id = verification_evidence.claim_id
              AND candidates.organization_id = current_org_id()
        )
    );

-- ── audit_logs ──
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_audit ON audit_logs
    USING (organization_id = current_org_id());

COMMIT;
