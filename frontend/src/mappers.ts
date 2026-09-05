import type { Candidate, Dashboard, Evidence, Job, ScreeningStatus, User } from "./types";

function num(value: unknown): number | null {
  if (value == null || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function list(value: unknown): string[] {
  if (Array.isArray(value)) return value.map((item) => String(item)).filter(Boolean);
  if (typeof value === "string" && value.trim()) {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function evidenceList(value: unknown): Evidence[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const row = item as Record<string, unknown>;
      const quote = str(row.quote || row.text || row.chunk);
      if (!quote) return null;
      return {
        quote,
        source: str(row.source || row.document || row.filename, "resume"),
        score: num(row.score ?? row.similarity ?? row.relevance),
      };
    })
    .filter((item): item is Evidence => item !== null);
}

function screeningStatus(raw: Record<string, unknown>): ScreeningStatus {
  const value = str(raw.screening_status || raw.pipeline_status);
  const allowed: ScreeningStatus[] = ["idle", "awaiting_resumes", "ready", "running", "done", "failed"];
  if (allowed.includes(value as ScreeningStatus)) return value as ScreeningStatus;
  if (raw.has_requirement && Number(raw.screened_count) > 0) return "done";
  if (raw.has_requirement && Number(raw.candidate_count) > 0) return "ready";
  if (raw.has_requirement) return "awaiting_resumes";
  return "idle";
}

export function mapUser(raw: Record<string, unknown>): User {
  return {
    id: (raw.id as number | string) ?? "",
    name: str(raw.name || raw.full_name, "Recruiter"),
    email: str(raw.email),
    role: str(raw.role, "recruiter"),
  };
}

export function mapJob(raw: Record<string, unknown>): Job {
  return {
    id: (raw.id as number | string) ?? "",
    title: str(raw.title || raw.role_title, "Untitled role"),
    department: str(raw.department),
    location: str(raw.location),
    employment_type: str(raw.employment_type || raw.type, "Full-time"),
    description: str(raw.description),
    requirement_filename: str(raw.requirement_filename || raw.jd_filename),
    has_requirement: Boolean(raw.has_requirement ?? raw.requirement_filename ?? raw.jd_text),
    required_skills: list(raw.required_skills || raw.skills),
    requirement_summary: str(raw.requirement_summary || raw.jd_summary),
    candidate_count: num(raw.candidate_count) ?? 0,
    screened_count: num(raw.screened_count) ?? 0,
    screening_status: screeningStatus(raw),
    created_at: raw.created_at ? str(raw.created_at) : null,
  };
}

export function mapCandidate(raw: Record<string, unknown>): Candidate {
  const overall = num(raw.overall_score ?? raw.rag_score ?? raw.score);
  return {
    id: (raw.id as number | string) ?? "",
    job_id: (raw.job_id as number | string) ?? raw.role_id ?? "",
    name: str(raw.name || raw.candidate_name, "Candidate"),
    email: str(raw.email),
    phone: str(raw.phone),
    filename: str(raw.filename || raw.resume_filename),
    status: str(raw.status, "uploaded"),
    skills: list(raw.skills),
    overall_score: overall,
    skill_score: num(raw.skill_score),
    experience_score: num(raw.experience_score),
    keyword_score: num(raw.keyword_score ?? raw.rag_score),
    rag_score: num(raw.rag_score ?? raw.overall_score ?? raw.score),
    matched_skills: list(raw.matched_skills),
    missing_skills: list(raw.missing_skills || raw.skill_gaps),
    years_experience: num(raw.years_experience),
    recommendation: str(raw.recommendation),
    summary: str(raw.summary || raw.rationale),
    evidence: evidenceList(raw.evidence || raw.citations || raw.chunks),
    created_at: raw.created_at ? str(raw.created_at) : null,
    resume_text: raw.resume_text ? str(raw.resume_text) : undefined,
  };
}

export function mapDashboard(raw: Record<string, unknown>): Dashboard {
  const recent = Array.isArray(raw.recent_jobs) ? raw.recent_jobs.map((job) => mapJob(job as Record<string, unknown>)) : [];
  return {
    jobs: num(raw.jobs) ?? 0,
    candidates: num(raw.candidates) ?? 0,
    screened: num(raw.screened) ?? 0,
    shortlisted: num(raw.shortlisted) ?? 0,
    avg_score: num(raw.avg_score) ?? 0,
    score_buckets: (raw.score_buckets as Record<string, number>) || {},
    recent_jobs: recent,
  };
}

export function mapToken(raw: Record<string, unknown>): { access_token: string } {
  const token = str(raw.access_token || raw.token || raw.accessToken);
  if (!token) throw new Error("Login succeeded but no access_token was returned");
  return { access_token: token };
}
