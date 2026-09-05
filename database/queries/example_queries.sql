-- ════════════════════════════════════════════════════════════════════════════
-- Example Queries for the AI Candidate Screening Platform
-- ════════════════════════════════════════════════════════════════════════════
-- Before running these queries, set the tenant context:
--   SET app.current_org_id = 'a0000000-0000-0000-0000-000000000001';
-- ════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────
-- 1. FIND TOP CANDIDATES FOR A JOB  (by screening score)
-- ──────────────────────────────────────────────────────────────────────────
-- Returns candidates ranked by overall_score for a given job.
SELECT
    c.full_name,
    c.email,
    c.location,
    sr.overall_score,
    sr.skill_match_score,
    sr.experience_match_score,
    sr.recommendation,
    sr.summary
FROM screening_results sr
JOIN candidates c ON c.id = sr.candidate_id
WHERE sr.job_id = 'c0000000-0000-0000-0000-000000000001'
ORDER BY sr.overall_score DESC NULLS LAST;


-- ──────────────────────────────────────────────────────────────────────────
-- 2. RETRIEVE ALL SKILLS FOR A CANDIDATE
-- ──────────────────────────────────────────────────────────────────────────
SELECT
    s.name            AS skill_name,
    s.category,
    cs.proficiency_level,
    cs.years_of_experience,
    cs.source
FROM candidate_skills cs
JOIN skills s ON s.id = cs.skill_id
WHERE cs.candidate_id = 'e0000000-0000-0000-0000-000000000001'
ORDER BY cs.years_of_experience DESC NULLS LAST;


-- ──────────────────────────────────────────────────────────────────────────
-- 3. RETRIEVE RESUME EVIDENCE FOR A SCREENING RESULT
-- ──────────────────────────────────────────────────────────────────────────
-- Shows all evidence items backing a particular screening decision.
SELECT
    ei.evidence_type,
    ei.confidence,
    ei.content,
    ei.source_reference
FROM evidence_items ei
WHERE ei.screening_result_id = 'aa000000-0000-0000-0000-000000000001'
ORDER BY
    CASE ei.confidence
        WHEN 'verified'     THEN 1
        WHEN 'supported'    THEN 2
        WHEN 'inconclusive' THEN 3
        WHEN 'contradicted' THEN 4
    END;


-- ──────────────────────────────────────────────────────────────────────────
-- 4. RETRIEVE VERIFICATION EVIDENCE FOR A CANDIDATE
-- ──────────────────────────────────────────────────────────────────────────
-- Shows all verification claims and their supporting evidence.
SELECT
    ep.platform,
    ep.profile_url,
    vc.claim_type,
    vc.claim_description,
    vc.status              AS claim_status,
    vc.confidence_score,
    ve.evidence_type,
    ve.evidence_url,
    ve.description         AS evidence_description
FROM external_profiles ep
JOIN verification_claims vc  ON vc.external_profile_id = ep.id
LEFT JOIN verification_evidence ve ON ve.claim_id = vc.id
WHERE ep.candidate_id = 'e0000000-0000-0000-0000-000000000001'
ORDER BY vc.status, vc.confidence_score DESC NULLS LAST;


-- ──────────────────────────────────────────────────────────────────────────
-- 5. VECTOR SIMILARITY SEARCH — Match resume chunks to a job requirement
-- ──────────────────────────────────────────────────────────────────────────
-- Find the top 5 resume chunks most similar to a given job requirement.
--
-- ⚠ This query only works after embeddings have been populated by the
--   AI agent.  The seed data leaves embeddings NULL.
--
-- Replace :query_embedding with the actual 1536-dim vector from your
-- embedding model (e.g. OpenAI text-embedding-3-small).
--
-- The <=> operator computes cosine distance (lower = more similar).

-- Example: Find resume chunks similar to a job requirement's embedding
SELECT
    rc.content,
    rc.section_type,
    r.file_name,
    c.full_name,
    rc.embedding <=> jr.embedding AS cosine_distance
FROM resume_chunks rc
JOIN resumes r    ON r.id  = rc.resume_id
JOIN candidates c ON c.id  = r.candidate_id
CROSS JOIN (
    SELECT embedding
    FROM job_requirements
    WHERE id = 'd0000000-0000-0000-0000-000000000001'  -- "Python programming" requirement
) jr
WHERE rc.embedding IS NOT NULL
  AND jr.embedding IS NOT NULL
ORDER BY cosine_distance ASC
LIMIT 5;

-- Alternate: Search with a raw embedding vector
-- SELECT
--     rc.content,
--     rc.section_type,
--     1 - (rc.embedding <=> :query_embedding) AS cosine_similarity
-- FROM resume_chunks rc
-- WHERE rc.embedding IS NOT NULL
-- ORDER BY rc.embedding <=> :query_embedding
-- LIMIT 10;


-- ──────────────────────────────────────────────────────────────────────────
-- 6. FIND SIMILAR SKILLS (vector similarity on skills table)
-- ──────────────────────────────────────────────────────────────────────────
-- Useful for matching "React" to "ReactJS" or "React.js".
-- SELECT
--     s.name,
--     s.category,
--     1 - (s.embedding <=> :query_embedding) AS similarity
-- FROM skills s
-- WHERE s.embedding IS NOT NULL
-- ORDER BY s.embedding <=> :query_embedding
-- LIMIT 5;


-- ──────────────────────────────────────────────────────────────────────────
-- 7. FULL CANDIDATE SCREENING REPORT
-- ──────────────────────────────────────────────────────────────────────────
-- Comprehensive view: screening + skill matches + gaps for one candidate/job.
SELECT
    c.full_name,
    j.title                     AS job_title,
    sr.overall_score,
    sr.recommendation,
    sr.summary                  AS screening_summary,
    -- Skill matches
    sm.match_strength,
    sk.name                     AS skill_name,
    sm.score                    AS match_score,
    sm.explanation,
    -- Gaps
    ga.gap_type,
    ga.severity,
    ga.description              AS gap_description,
    ga.suggestion
FROM screening_results sr
JOIN candidates c  ON c.id  = sr.candidate_id
JOIN jobs j        ON j.id  = sr.job_id
LEFT JOIN skill_matches sm ON sm.screening_result_id = sr.id
LEFT JOIN skills sk        ON sk.id = sm.skill_id
LEFT JOIN gap_analysis ga  ON ga.screening_result_id = sr.id
WHERE sr.job_id       = 'c0000000-0000-0000-0000-000000000001'
  AND sr.candidate_id = 'e0000000-0000-0000-0000-000000000001'
ORDER BY sm.score DESC NULLS LAST;


-- ──────────────────────────────────────────────────────────────────────────
-- 8. CANDIDATE WORK HISTORY + PROJECTS
-- ──────────────────────────────────────────────────────────────────────────
SELECT
    c.full_name,
    e.company_name,
    e.job_title,
    e.start_date,
    e.end_date,
    e.is_current,
    e.description
FROM experiences e
JOIN candidates c ON c.id = e.candidate_id
WHERE c.id = 'e0000000-0000-0000-0000-000000000001'
ORDER BY e.start_date DESC;

SELECT
    c.full_name,
    p.title        AS project_title,
    p.description,
    p.url,
    p.technologies
FROM projects p
JOIN candidates c ON c.id = p.candidate_id
WHERE c.id = 'e0000000-0000-0000-0000-000000000001';


-- ──────────────────────────────────────────────────────────────────────────
-- 9. GAP ANALYSIS — What is a candidate missing for a job?
-- ──────────────────────────────────────────────────────────────────────────
SELECT
    c.full_name,
    j.title         AS job_title,
    jr.description  AS requirement,
    ga.gap_type,
    ga.severity,
    ga.description  AS gap_description,
    ga.suggestion
FROM gap_analysis ga
JOIN screening_results sr ON sr.id = ga.screening_result_id
JOIN candidates c         ON c.id  = sr.candidate_id
JOIN jobs j               ON j.id  = sr.job_id
JOIN job_requirements jr  ON jr.id = ga.job_requirement_id
WHERE sr.candidate_id = 'e0000000-0000-0000-0000-000000000002'
  AND sr.job_id       = 'c0000000-0000-0000-0000-000000000001'
ORDER BY
    CASE ga.severity
        WHEN 'critical' THEN 1
        WHEN 'major'    THEN 2
        WHEN 'minor'    THEN 3
    END;


-- ──────────────────────────────────────────────────────────────────────────
-- 10. AUDIT LOG — Recent actions for the current organization
-- ──────────────────────────────────────────────────────────────────────────
SELECT
    al.action,
    al.entity_type,
    al.entity_id,
    u.full_name    AS performed_by,
    al.new_values,
    al.created_at
FROM audit_logs al
LEFT JOIN users u ON u.id = al.user_id
WHERE al.organization_id = 'a0000000-0000-0000-0000-000000000001'
ORDER BY al.created_at DESC
LIMIT 20;


-- ──────────────────────────────────────────────────────────────────────────
-- 11. CANDIDATES WITH UNVERIFIED CLAIMS  (for verification queue)
-- ──────────────────────────────────────────────────────────────────────────
SELECT
    c.full_name,
    c.email,
    ep.platform,
    vc.claim_type,
    vc.claim_description,
    vc.status
FROM verification_claims vc
JOIN external_profiles ep ON ep.id = vc.external_profile_id
JOIN candidates c         ON c.id  = ep.candidate_id
WHERE vc.status = 'pending'
ORDER BY vc.created_at ASC;
