-- Migration 002: Custom ENUM Types
-- ============================================
-- Centralised type definitions keep CHECK constraints DRY
-- and give the query planner richer metadata.

BEGIN;

-- User roles within an organization
CREATE TYPE user_role AS ENUM (
    'admin',
    'recruiter',
    'viewer'
);

-- Job lifecycle status
CREATE TYPE job_status AS ENUM (
    'draft',
    'open',
    'closed',
    'archived'
);

-- Employment type for jobs
CREATE TYPE employment_type AS ENUM (
    'full_time',
    'part_time',
    'contract',
    'internship'
);

-- Candidate pipeline status
CREATE TYPE candidate_status AS ENUM (
    'new',
    'screening',
    'screened',
    'shortlisted',
    'rejected',
    'hired'
);

-- Job requirement categories
CREATE TYPE requirement_type AS ENUM (
    'skill',
    'experience',
    'education',
    'certification'
);

-- Resume chunk sections
CREATE TYPE section_type AS ENUM (
    'summary',
    'experience',
    'education',
    'skills',
    'projects',
    'certifications',
    'other'
);

-- Skill proficiency levels
CREATE TYPE proficiency_level AS ENUM (
    'beginner',
    'intermediate',
    'advanced',
    'expert'
);

-- Where a skill claim came from
CREATE TYPE skill_source AS ENUM (
    'resume',
    'self_reported',
    'verified',
    'inferred'
);

-- Screening recommendation
CREATE TYPE screening_recommendation AS ENUM (
    'strong_match',
    'good_match',
    'partial_match',
    'weak_match'
);

-- Match strength between a requirement and a candidate attribute
CREATE TYPE match_strength AS ENUM (
    'exact',
    'strong',
    'partial',
    'none'
);

-- Evidence confidence level
-- "Not found" ≠ "false": INCONCLUSIVE is the correct default.
CREATE TYPE confidence_level AS ENUM (
    'verified',
    'supported',
    'inconclusive',
    'contradicted'
);

-- Gap severity
CREATE TYPE gap_severity AS ENUM (
    'critical',
    'major',
    'minor'
);

-- Gap categories
CREATE TYPE gap_type AS ENUM (
    'missing_skill',
    'insufficient_experience',
    'missing_certification',
    'missing_education'
);

-- External profile platforms
CREATE TYPE platform_type AS ENUM (
    'github',
    'linkedin',
    'stackoverflow',
    'portfolio',
    'other'
);

-- Verification claim categories
CREATE TYPE claim_type AS ENUM (
    'skill',
    'experience',
    'project',
    'education',
    'contribution'
);

-- Verification claim status
-- Mirrors confidence_level but adds 'pending' for unprocessed claims.
CREATE TYPE verification_status AS ENUM (
    'pending',
    'verified',
    'supported',
    'inconclusive',
    'contradicted'
);

-- Evidence sources for verification
CREATE TYPE evidence_source_type AS ENUM (
    'github_repo',
    'github_commit',
    'github_pr',
    'linkedin_endorsement',
    'portfolio_item',
    'code_sample',
    'other'
);

-- Evidence types for screening
CREATE TYPE evidence_item_type AS ENUM (
    'resume_excerpt',
    'project',
    'experience',
    'skill_match',
    'external_profile'
);

COMMIT;
