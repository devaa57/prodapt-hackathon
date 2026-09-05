-- Migration 010: Seed Data
-- ============================================================================
-- Realistic sample data for local development and demo.
-- Uses fixed UUIDs so that example queries can reference them.
--
-- ⚠ DO NOT run this in production.

BEGIN;

-- ════════════════════════════════════════════
-- 1. ORGANIZATIONS
-- ════════════════════════════════════════════
INSERT INTO organizations (id, name, slug, domain) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Prodapt Technologies',  'prodapt',   'prodapt.com'),
    ('a0000000-0000-0000-0000-000000000002', 'Acme Corp',             'acme-corp', 'acme.com');

-- ════════════════════════════════════════════
-- 2. USERS
-- ════════════════════════════════════════════
INSERT INTO users (id, organization_id, email, full_name, role) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'alice@prodapt.com',  'Alice Menon',   'admin'),
    ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'bob@prodapt.com',    'Bob Sharma',    'recruiter'),
    ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000002', 'carol@acme.com',     'Carol Davis',   'admin');

-- ════════════════════════════════════════════
-- 3. JOBS
-- ════════════════════════════════════════════
INSERT INTO jobs (id, organization_id, created_by, title, description, department, location, employment_type, status) VALUES
    ('c0000000-0000-0000-0000-000000000001',
     'a0000000-0000-0000-0000-000000000001',
     'b0000000-0000-0000-0000-000000000001',
     'Senior Python Developer',
     'We are looking for an experienced Python developer to build AI-powered microservices. '
     'The ideal candidate has strong experience with FastAPI, PostgreSQL, and LLM integration.',
     'Engineering', 'Bangalore, India', 'full_time', 'open'),

    ('c0000000-0000-0000-0000-000000000002',
     'a0000000-0000-0000-0000-000000000001',
     'b0000000-0000-0000-0000-000000000002',
     'Full Stack Engineer',
     'Build and maintain our customer-facing web application using React and Node.js. '
     'Experience with TypeScript and cloud platforms preferred.',
     'Engineering', 'Chennai, India', 'full_time', 'open');

-- ════════════════════════════════════════════
-- 4. JOB REQUIREMENTS
-- ════════════════════════════════════════════
INSERT INTO job_requirements (id, job_id, requirement_type, description, is_mandatory, min_years) VALUES
    ('d0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'skill',       'Python programming',                    true,  3),
    ('d0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001', 'skill',       'FastAPI or Django REST framework',       true,  2),
    ('d0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001', 'skill',       'PostgreSQL and database design',         true,  2),
    ('d0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000001', 'skill',       'LLM integration (OpenAI, LangChain)',    false, NULL),
    ('d0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000001', 'experience',  'Experience in agile software teams',     false, 2),
    ('d0000000-0000-0000-0000-000000000006', 'c0000000-0000-0000-0000-000000000002', 'skill',       'React.js',                              true,  2),
    ('d0000000-0000-0000-0000-000000000007', 'c0000000-0000-0000-0000-000000000002', 'skill',       'TypeScript',                            true,  1),
    ('d0000000-0000-0000-0000-000000000008', 'c0000000-0000-0000-0000-000000000002', 'skill',       'Node.js / Express',                     true,  2);

-- ════════════════════════════════════════════
-- 5. CANDIDATES
-- ════════════════════════════════════════════
INSERT INTO candidates (id, organization_id, email, full_name, phone, location, source, status) VALUES
    ('e0000000-0000-0000-0000-000000000001',
     'a0000000-0000-0000-0000-000000000001',
     'ravi.kumar@email.com', 'Ravi Kumar', '+91-9876543210', 'Bangalore, India', 'career_page', 'screened'),

    ('e0000000-0000-0000-0000-000000000002',
     'a0000000-0000-0000-0000-000000000001',
     'priya.patel@email.com', 'Priya Patel', '+91-9123456789', 'Mumbai, India', 'referral', 'screening'),

    ('e0000000-0000-0000-0000-000000000003',
     'a0000000-0000-0000-0000-000000000001',
     'arjun.das@email.com', 'Arjun Das', '+91-9988776655', 'Chennai, India', 'linkedin', 'new');

-- ════════════════════════════════════════════
-- 6. RESUMES
-- ════════════════════════════════════════════
INSERT INTO resumes (id, candidate_id, file_name, file_url, raw_text, language) VALUES
    ('f0000000-0000-0000-0000-000000000001',
     'e0000000-0000-0000-0000-000000000001',
     'ravi_kumar_resume.pdf', '/uploads/resumes/ravi_kumar_resume.pdf',
     'Ravi Kumar — Senior Software Engineer with 5+ years of experience in Python, FastAPI, and PostgreSQL. '
     'Built AI-powered microservices at TechStartup Inc. Led migration from monolith to microservices. '
     'Experience with LangChain, OpenAI APIs, Docker, and Kubernetes. '
     'Education: B.Tech Computer Science, IIT Madras (2018).',
     'en'),

    ('f0000000-0000-0000-0000-000000000002',
     'e0000000-0000-0000-0000-000000000002',
     'priya_patel_resume.pdf', '/uploads/resumes/priya_patel_resume.pdf',
     'Priya Patel — Full Stack Developer with 3 years experience. '
     'Skilled in React, TypeScript, Node.js, Python, and MongoDB. '
     'Built e-commerce platform serving 10K+ users. Contributed to open-source React component library. '
     'Education: M.Sc. Computer Science, University of Mumbai (2021).',
     'en');

-- ════════════════════════════════════════════
-- 7. RESUME CHUNKS
-- ════════════════════════════════════════════
-- Embeddings are NULL because they require an LLM API call.
-- The AI agent will populate them at runtime.
INSERT INTO resume_chunks (id, resume_id, chunk_index, content, section_type) VALUES
    ('f1000000-0000-0000-0000-000000000001', 'f0000000-0000-0000-0000-000000000001', 0,
     'Senior Software Engineer with 5+ years of experience in Python, FastAPI, and PostgreSQL.',
     'summary'),
    ('f1000000-0000-0000-0000-000000000002', 'f0000000-0000-0000-0000-000000000001', 1,
     'Built AI-powered microservices at TechStartup Inc. Led migration from monolith to microservices.',
     'experience'),
    ('f1000000-0000-0000-0000-000000000003', 'f0000000-0000-0000-0000-000000000001', 2,
     'Experience with LangChain, OpenAI APIs, Docker, and Kubernetes.',
     'skills'),
    ('f1000000-0000-0000-0000-000000000004', 'f0000000-0000-0000-0000-000000000002', 0,
     'Full Stack Developer with 3 years experience. Skilled in React, TypeScript, Node.js, Python.',
     'summary'),
    ('f1000000-0000-0000-0000-000000000005', 'f0000000-0000-0000-0000-000000000002', 1,
     'Built e-commerce platform serving 10K+ users. Contributed to open-source React component library.',
     'experience');

-- ════════════════════════════════════════════
-- 8. SKILLS  (canonical list)
-- ════════════════════════════════════════════
INSERT INTO skills (id, name, category) VALUES
    ('50000000-0000-0000-0000-000000000001', 'Python',          'programming_language'),
    ('50000000-0000-0000-0000-000000000002', 'FastAPI',         'framework'),
    ('50000000-0000-0000-0000-000000000003', 'PostgreSQL',      'database'),
    ('50000000-0000-0000-0000-000000000004', 'LangChain',       'framework'),
    ('50000000-0000-0000-0000-000000000005', 'React',           'framework'),
    ('50000000-0000-0000-0000-000000000006', 'TypeScript',      'programming_language'),
    ('50000000-0000-0000-0000-000000000007', 'Node.js',         'runtime'),
    ('50000000-0000-0000-0000-000000000008', 'Docker',          'devops'),
    ('50000000-0000-0000-0000-000000000009', 'Kubernetes',      'devops'),
    ('50000000-0000-0000-0000-000000000010', 'MongoDB',         'database'),
    ('50000000-0000-0000-0000-000000000011', 'Django',          'framework'),
    ('50000000-0000-0000-0000-000000000012', 'OpenAI API',      'ai_ml');

-- ════════════════════════════════════════════
-- 9. CANDIDATE SKILLS
-- ════════════════════════════════════════════
INSERT INTO candidate_skills (id, candidate_id, skill_id, proficiency_level, years_of_experience, source) VALUES
    -- Ravi Kumar
    ('60000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'expert',       5.0, 'resume'),
    ('60000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000002', 'advanced',     3.0, 'resume'),
    ('60000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000003', 'advanced',     4.0, 'resume'),
    ('60000000-0000-0000-0000-000000000004', 'e0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000004', 'intermediate', 1.0, 'resume'),
    ('60000000-0000-0000-0000-000000000005', 'e0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000008', 'advanced',     3.0, 'resume'),
    -- Priya Patel
    ('60000000-0000-0000-0000-000000000006', 'e0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000005', 'advanced',     3.0, 'resume'),
    ('60000000-0000-0000-0000-000000000007', 'e0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000006', 'intermediate', 2.0, 'resume'),
    ('60000000-0000-0000-0000-000000000008', 'e0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000007', 'advanced',     3.0, 'resume'),
    ('60000000-0000-0000-0000-000000000009', 'e0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000001', 'intermediate', 1.5, 'resume'),
    ('60000000-0000-0000-0000-000000000010', 'e0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000010', 'intermediate', 2.0, 'resume');

-- ════════════════════════════════════════════
-- 10. EXPERIENCES
-- ════════════════════════════════════════════
INSERT INTO experiences (id, candidate_id, company_name, job_title, location, start_date, end_date, is_current, description) VALUES
    ('70000000-0000-0000-0000-000000000001',
     'e0000000-0000-0000-0000-000000000001',
     'TechStartup Inc.', 'Senior Software Engineer', 'Bangalore, India',
     '2021-06-01', NULL, true,
     'Building AI-powered microservices. Led monolith-to-microservices migration. Integrated LLM workflows.'),

    ('70000000-0000-0000-0000-000000000002',
     'e0000000-0000-0000-0000-000000000001',
     'Infosys', 'Software Engineer', 'Pune, India',
     '2018-07-01', '2021-05-31', false,
     'Developed REST APIs using Python/Django. Managed PostgreSQL databases for enterprise clients.'),

    ('70000000-0000-0000-0000-000000000003',
     'e0000000-0000-0000-0000-000000000002',
     'WebWorks Digital', 'Full Stack Developer', 'Mumbai, India',
     '2021-09-01', NULL, true,
     'Built e-commerce platform with React + Node.js. Implemented CI/CD pipelines.');

-- ════════════════════════════════════════════
-- 11. PROJECTS
-- ════════════════════════════════════════════
INSERT INTO projects (id, candidate_id, title, description, url, technologies) VALUES
    ('80000000-0000-0000-0000-000000000001',
     'e0000000-0000-0000-0000-000000000001',
     'AI Resume Analyzer',
     'Open-source tool that uses LLMs to parse and score resumes against job descriptions.',
     'https://github.com/ravikumar/ai-resume-analyzer',
     ARRAY['Python', 'FastAPI', 'LangChain', 'PostgreSQL']),

    ('80000000-0000-0000-0000-000000000002',
     'e0000000-0000-0000-0000-000000000002',
     'React Component Library',
     'Open-source UI component library with 200+ GitHub stars.',
     'https://github.com/priyapatel/react-ui-kit',
     ARRAY['React', 'TypeScript', 'Storybook']);

-- ════════════════════════════════════════════
-- 12. EXTERNAL PROFILES
-- ════════════════════════════════════════════
INSERT INTO external_profiles (id, candidate_id, platform, profile_url, username) VALUES
    ('90000000-0000-0000-0000-000000000001',
     'e0000000-0000-0000-0000-000000000001',
     'github', 'https://github.com/ravikumar', 'ravikumar'),

    ('90000000-0000-0000-0000-000000000002',
     'e0000000-0000-0000-0000-000000000002',
     'github', 'https://github.com/priyapatel', 'priyapatel');

-- ════════════════════════════════════════════
-- 13. VERIFICATION CLAIMS
-- ════════════════════════════════════════════
INSERT INTO verification_claims (id, external_profile_id, claim_type, claim_description, status, confidence_score, verified_at) VALUES
    ('91000000-0000-0000-0000-000000000001',
     '90000000-0000-0000-0000-000000000001',
     'project', 'Candidate claims to have built an AI Resume Analyzer using Python and LangChain',
     'verified', 92.50, now() - INTERVAL '1 day'),

    ('91000000-0000-0000-0000-000000000002',
     '90000000-0000-0000-0000-000000000001',
     'skill', 'Candidate claims expert-level Python proficiency',
     'supported', 85.00, now() - INTERVAL '1 day'),

    ('91000000-0000-0000-0000-000000000003',
     '90000000-0000-0000-0000-000000000002',
     'project', 'Candidate claims to maintain a React component library with 200+ stars',
     'verified', 95.00, now() - INTERVAL '2 days'),

    ('91000000-0000-0000-0000-000000000004',
     '90000000-0000-0000-0000-000000000002',
     'skill', 'Candidate claims Kubernetes experience',
     'inconclusive', NULL, NULL);  -- Not found ≠ false!

-- ════════════════════════════════════════════
-- 14. VERIFICATION EVIDENCE
-- ════════════════════════════════════════════
INSERT INTO verification_evidence (id, claim_id, evidence_type, evidence_url, description) VALUES
    ('92000000-0000-0000-0000-000000000001',
     '91000000-0000-0000-0000-000000000001',
     'github_repo',
     'https://github.com/ravikumar/ai-resume-analyzer',
     'Public repository with 45 commits, using Python, FastAPI, and LangChain. Last commit 2 weeks ago.'),

    ('92000000-0000-0000-0000-000000000002',
     '91000000-0000-0000-0000-000000000002',
     'github_commit',
     'https://github.com/ravikumar',
     'GitHub profile shows 320+ contributions in the last year, primarily in Python repositories.'),

    ('92000000-0000-0000-0000-000000000003',
     '91000000-0000-0000-0000-000000000003',
     'github_repo',
     'https://github.com/priyapatel/react-ui-kit',
     'Repository has 215 stars, 30 forks, and active maintenance. TypeScript usage at 89%.');

-- ════════════════════════════════════════════
-- 15. SCREENING RESULTS
-- ════════════════════════════════════════════
INSERT INTO screening_results (id, job_id, candidate_id, overall_score, skill_match_score, experience_match_score, summary, recommendation, screened_by) VALUES
    ('aa000000-0000-0000-0000-000000000001',
     'c0000000-0000-0000-0000-000000000001',
     'e0000000-0000-0000-0000-000000000001',
     88.50, 92.00, 85.00,
     'Strong match for Senior Python Developer. Candidate has 5+ years Python experience, '
     'direct FastAPI and PostgreSQL skills, and demonstrated LLM integration experience. '
     'Verified GitHub activity supports claims.',
     'strong_match', 'ai_agent'),

    ('aa000000-0000-0000-0000-000000000002',
     'c0000000-0000-0000-0000-000000000001',
     'e0000000-0000-0000-0000-000000000002',
     52.00, 45.00, 60.00,
     'Partial match. Candidate has Python experience but primarily a frontend developer. '
     'Limited FastAPI or PostgreSQL experience. Strong React/TypeScript skills not directly relevant.',
     'partial_match', 'ai_agent');

-- ════════════════════════════════════════════
-- 16. SKILL MATCHES
-- ════════════════════════════════════════════
INSERT INTO skill_matches (id, screening_result_id, skill_id, job_requirement_id, candidate_skill_id, match_strength, score, explanation) VALUES
    -- Ravi Kumar vs Senior Python Developer
    ('ab000000-0000-0000-0000-000000000001', 'aa000000-0000-0000-0000-000000000001',
     '50000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000001',
     'exact', 98.00, 'Expert Python with 5 years — exceeds 3-year requirement.'),

    ('ab000000-0000-0000-0000-000000000002', 'aa000000-0000-0000-0000-000000000001',
     '50000000-0000-0000-0000-000000000002', 'd0000000-0000-0000-0000-000000000002', '60000000-0000-0000-0000-000000000002',
     'exact', 95.00, 'Advanced FastAPI with 3 years — exceeds 2-year requirement.'),

    ('ab000000-0000-0000-0000-000000000003', 'aa000000-0000-0000-0000-000000000001',
     '50000000-0000-0000-0000-000000000003', 'd0000000-0000-0000-0000-000000000003', '60000000-0000-0000-0000-000000000003',
     'exact', 95.00, 'Advanced PostgreSQL with 4 years — exceeds 2-year requirement.');

-- ════════════════════════════════════════════
-- 17. EVIDENCE ITEMS
-- ════════════════════════════════════════════
INSERT INTO evidence_items (id, screening_result_id, evidence_type, content, source_reference, confidence) VALUES
    ('ac000000-0000-0000-0000-000000000001', 'aa000000-0000-0000-0000-000000000001',
     'resume_excerpt',
     'Senior Software Engineer with 5+ years of experience in Python, FastAPI, and PostgreSQL.',
     'resume chunk #0', 'supported'),

    ('ac000000-0000-0000-0000-000000000002', 'aa000000-0000-0000-0000-000000000001',
     'external_profile',
     'GitHub profile shows 320+ contributions, primarily Python. Active AI Resume Analyzer project.',
     'https://github.com/ravikumar', 'verified'),

    ('ac000000-0000-0000-0000-000000000003', 'aa000000-0000-0000-0000-000000000001',
     'experience',
     'Built AI-powered microservices at TechStartup Inc. Led monolith-to-microservices migration.',
     'resume chunk #1', 'supported');

-- ════════════════════════════════════════════
-- 18. GAP ANALYSIS
-- ════════════════════════════════════════════
INSERT INTO gap_analysis (id, screening_result_id, job_requirement_id, gap_type, severity, description, suggestion) VALUES
    ('ad000000-0000-0000-0000-000000000001',
     'aa000000-0000-0000-0000-000000000002',
     'd0000000-0000-0000-0000-000000000002',
     'missing_skill', 'critical',
     'No FastAPI or Django REST framework experience found in resume.',
     'Consider if candidate''s Node.js/Express API experience is transferable.'),

    ('ad000000-0000-0000-0000-000000000002',
     'aa000000-0000-0000-0000-000000000002',
     'd0000000-0000-0000-0000-000000000003',
     'insufficient_experience', 'major',
     'Resume mentions MongoDB but no PostgreSQL experience.',
     'Candidate may have basic SQL knowledge — consider technical assessment.');

-- ════════════════════════════════════════════
-- 19. AUDIT LOG SAMPLES
-- ════════════════════════════════════════════
INSERT INTO audit_logs (organization_id, user_id, action, entity_type, entity_id, new_values) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001',
     'create', 'job', 'c0000000-0000-0000-0000-000000000001',
     '{"title": "Senior Python Developer", "status": "open"}'::JSONB),

    ('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002',
     'create', 'candidate', 'e0000000-0000-0000-0000-000000000001',
     '{"full_name": "Ravi Kumar", "source": "career_page"}'::JSONB),

    ('a0000000-0000-0000-0000-000000000001', NULL,
     'screen', 'screening_result', 'aa000000-0000-0000-0000-000000000001',
     '{"overall_score": 88.50, "recommendation": "strong_match", "screened_by": "ai_agent"}'::JSONB);

COMMIT;
