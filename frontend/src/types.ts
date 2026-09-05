export type ScreeningStatus = "idle" | "awaiting_resumes" | "ready" | "running" | "done" | "failed";

export type Evidence = {
  quote: string;
  source: string;
  score: number | null;
};

export type User = {
  id: number | string;
  name: string;
  email: string;
  role: string;
};

export type Job = {
  id: number | string;
  title: string;
  department: string;
  location: string;
  employment_type: string;
  description: string;
  requirement_filename: string;
  has_requirement: boolean;
  required_skills: string[];
  requirement_summary: string;
  candidate_count: number;
  screened_count: number;
  screening_status: ScreeningStatus;
  created_at: string | null;
};

export type Candidate = {
  id: number | string;
  job_id: number | string;
  name: string;
  email: string;
  phone: string;
  filename: string;
  status: string;
  skills: string[];
  overall_score: number | null;
  skill_score: number | null;
  experience_score: number | null;
  keyword_score: number | null;
  rag_score: number | null;
  matched_skills: string[];
  missing_skills: string[];
  years_experience: number | null;
  recommendation: string;
  summary: string;
  evidence: Evidence[];
  created_at: string | null;
  resume_text?: string;
};

export type Dashboard = {
  jobs: number;
  candidates: number;
  screened: number;
  shortlisted: number;
  avg_score: number;
  score_buckets: Record<string, number>;
  recent_jobs: Job[];
};
