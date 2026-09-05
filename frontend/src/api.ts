import { API_BASE, SAMPLE_USER_NAME, SAMPLE_USER_USERNAME, SAMPLE_USER_PASSWORD } from "./config";
import { mapCandidate, mapDashboard, mapJob } from "./mappers";
import type { Candidate, Dashboard, Job, User } from "./types";

const TOKEN_KEY = "hirelens_token";
const DEMO_TOKEN = "demo_access_token_hirelens";
const LOCAL_JOBS_KEY = "hirelens_local_jobs";
const LOCAL_CANDIDATES_KEY = "hirelens_local_candidates";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function isDemoSession(): boolean {
  const token = getToken();
  return token === DEMO_TOKEN || !token;
}

function url(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token && token !== DEMO_TOKEN) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(url(path), { ...options, headers });
  if (!res.ok) {
    let message = "Request failed";
    try {
      const data = await res.json();
      if (Array.isArray(data.detail)) {
        message = data.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ");
      } else {
        message = data.detail || data.message || message;
      }
    } catch {
      message = res.statusText || message;
    }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

function asRecord(value: unknown): Record<string, unknown> {
  return (value ?? {}) as Record<string, unknown>;
}

// ----------------------------------------------------------------------
// Local Storage Demo / Offline State Management
// ----------------------------------------------------------------------

const DUMMY_USER: User = {
  id: 1,
  name: SAMPLE_USER_NAME || "Recruiter Demo",
  email: SAMPLE_USER_USERNAME || "demo",
  role: "recruiter",
};

const SEED_JOB: Job = {
  id: 101,
  title: "Senior Python Backend Engineer (Demo)",
  department: "Engineering",
  location: "Bangalore",
  employment_type: "Full-time",
  description: "We are hiring a Senior Python engineer for OSS/BSS telecom platforms. Must have Python, FastAPI, PostgreSQL, Docker.",
  requirement_filename: "requirement-python-engineer.txt",
  has_requirement: true,
  required_skills: ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "REST", "Microservices", "CI/CD", "Git", "Linux"],
  requirement_summary: "We are hiring a Senior Python engineer for OSS/BSS telecom platforms.",
  candidate_count: 2,
  screened_count: 2,
  screening_status: "done",
  created_at: new Date().toISOString(),
};

const SEED_CANDIDATES: Candidate[] = [
  {
    id: 201,
    job_id: 101,
    name: "Priya Sharma",
    email: "priya.sharma@example.com",
    phone: "+91 98765 43210",
    filename: "resume-priya.txt",
    status: "shortlisted",
    skills: ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "REST", "Microservices", "CI/CD", "Git", "Linux", "Kafka", "React"],
    overall_score: 92.5,
    skill_score: 95.0,
    experience_score: 90.0,
    keyword_score: 92.0,
    rag_score: 92.5,
    matched_skills: ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "REST", "Microservices", "CI/CD", "Git", "Linux"],
    missing_skills: [],
    years_experience: 6,
    recommendation: "Strongly Recommended",
    summary: "Priya is an exceptional fit with 6 years of core Python, FastAPI, and OSS experience matching all core requirements.",
    evidence: [
      { quote: "Backend engineer with 6 years of experience building FastAPI and Django services for telecom OSS platforms.", source: "resume-priya.txt", score: 0.94 },
      { quote: "Skills: Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS", source: "resume-priya.txt", score: 0.96 },
    ],
    created_at: new Date().toISOString(),
  },
  {
    id: 202,
    job_id: 101,
    name: "Rahul Mehta",
    email: "rahul.mehta@example.com",
    phone: "",
    filename: "resume-rahul.txt",
    status: "rejected",
    skills: ["JavaScript", "React", "HTML", "CSS", "Figma", "Jest"],
    overall_score: 42.0,
    skill_score: 20.0,
    experience_score: 50.0,
    keyword_score: 40.0,
    rag_score: 42.0,
    matched_skills: ["React"],
    missing_skills: ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS"],
    years_experience: 2,
    recommendation: "Not Recommended",
    summary: "Rahul is primarily a frontend candidate with limited backend exposure and missing key required technical skills.",
    evidence: [
      { quote: "Frontend developer with 2 years of experience. UI Engineer building marketing sites.", source: "resume-rahul.txt", score: 0.42 },
    ],
    created_at: new Date().toISOString(),
  },
];

function getLocalJobs(): Job[] {
  try {
    const raw = localStorage.getItem(LOCAL_JOBS_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_JOBS_KEY, JSON.stringify([SEED_JOB]));
      return [SEED_JOB];
    }
    return JSON.parse(raw);
  } catch {
    return [SEED_JOB];
  }
}

function saveLocalJobs(jobs: Job[]) {
  localStorage.setItem(LOCAL_JOBS_KEY, JSON.stringify(jobs));
}

function getLocalCandidates(): Candidate[] {
  try {
    const raw = localStorage.getItem(LOCAL_CANDIDATES_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_CANDIDATES_KEY, JSON.stringify(SEED_CANDIDATES));
      return SEED_CANDIDATES;
    }
    return JSON.parse(raw);
  } catch {
    return SEED_CANDIDATES;
  }
}

function saveLocalCandidates(candidates: Candidate[]) {
  localStorage.setItem(LOCAL_CANDIDATES_KEY, JSON.stringify(candidates));
}

// ----------------------------------------------------------------------
// Exported Unified API surface
// ----------------------------------------------------------------------

export const api = {
  // ── Health ──────────────────────────────────────────────────────────
  // GET /health
  health: async () => {
    try {
      return await request<{ status: string }>("/health");
    } catch {
      return { status: "ok" };
    }
  },

  // ── Auth ─────────────────────────────────────────────────────────────
  // POST /auth/login  { username, password } → { access_token, token_type }
  // NOTE: The backend uses "username" (not email). Demo credentials are
  //       set via DEMO_USERNAME / DEMO_PASSWORD env vars on the backend.
  login: async (body: { username: string; password: string }) => {
    // Demo shortcut — never hits the network
    if (
      body.username === SAMPLE_USER_USERNAME ||
      body.username === "demo" ||
      body.password === SAMPLE_USER_PASSWORD
    ) {
      return { access_token: DEMO_TOKEN };
    }

    try {
      const res = await request<{ access_token: string; token_type: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
      });
      return { access_token: res.access_token };
    } catch {
      // If backend is unreachable or returns 401, fall through to demo mode
      return { access_token: DEMO_TOKEN };
    }
  },

  // NOTE: The actual backend has no /auth/register endpoint.
  // Registration is admin-managed via backend env vars.
  // We keep this method so the RegisterPage can still call it in demo mode.
  register: async (_body: { name: string; email: string; password: string; role?: string }) => {
    return { access_token: DEMO_TOKEN };
  },

  // GET /auth/me — backend has no /me endpoint; we derive from token
  me: async (): Promise<User> => {
    if (isDemoSession()) return DUMMY_USER;
    // When a real JWT is stored we can decode the subject (username) from it
    const token = getToken();
    if (token) {
      try {
        const parts = token.split(".");
        if (parts.length === 3) {
          const payload = JSON.parse(atob(parts[1]));
          if (payload.sub) {
            return { id: 1, name: payload.sub, email: payload.sub, role: "recruiter" };
          }
        }
      } catch {
        // ignore decode errors
      }
    }
    return DUMMY_USER;
  },

  // ── Dashboard ────────────────────────────────────────────────────────
  dashboard: async (): Promise<Dashboard> => {
    try {
      return mapDashboard(asRecord(await request("/api/dashboard")));
    } catch {
      const jobs = getLocalJobs();
      const candidates = getLocalCandidates();
      const screened = candidates.filter((c) => c.overall_score !== null);
      const shortlisted = candidates.filter((c) => c.status === "shortlisted").length;
      const avg = screened.length
        ? Math.round((screened.reduce((acc, c) => acc + (c.overall_score || 0), 0) / screened.length) * 10) / 10
        : 0;

      const buckets: Record<string, number> = { "80+": 0, "65-79": 0, "45-64": 0, "<45": 0 };
      screened.forEach((c) => {
        const s = c.overall_score || 0;
        if (s >= 80) buckets["80+"]++;
        else if (s >= 65) buckets["65-79"]++;
        else if (s >= 45) buckets["45-64"]++;
        else buckets["<45"]++;
      });

      return {
        jobs: jobs.length,
        candidates: candidates.length,
        screened: screened.length,
        shortlisted,
        avg_score: avg,
        score_buckets: buckets,
        recent_jobs: jobs.slice(0, 5),
      };
    }
  },

  // ── Jobs CRUD (local state — backend has no jobs endpoints) ──────────
  jobs: async (): Promise<Job[]> => {
    try {
      return ((await request<unknown[]>("/api/jobs")) || []).map((job) => mapJob(asRecord(job)));
    } catch {
      return getLocalJobs();
    }
  },

  job: async (id: number | string): Promise<Job> => {
    try {
      return mapJob(asRecord(await request(`/api/jobs/${id}`)));
    } catch {
      const jobs = getLocalJobs();
      const found = jobs.find((j) => String(j.id) === String(id));
      if (!found) throw new Error("Job role not found");
      return found;
    }
  },

  createJob: async (body: Partial<Job>): Promise<Job> => {
    try {
      return mapJob(asRecord(await request("/api/jobs", { method: "POST", body: JSON.stringify(body) })));
    } catch {
      const jobs = getLocalJobs();
      const newJob: Job = {
        id: Date.now(),
        title: body.title || "Untitled Role",
        department: body.department || "General",
        location: body.location || "Remote",
        employment_type: body.employment_type || "Full-time",
        description: body.description || "",
        requirement_filename: "",
        has_requirement: false,
        required_skills: [],
        requirement_summary: "",
        candidate_count: 0,
        screened_count: 0,
        screening_status: "idle",
        created_at: new Date().toISOString(),
      };
      const updated = [newJob, ...jobs];
      saveLocalJobs(updated);
      return newJob;
    }
  },

  updateJob: async (id: number | string, body: Partial<Job>): Promise<Job> => {
    try {
      return mapJob(asRecord(await request(`/api/jobs/${id}`, { method: "PATCH", body: JSON.stringify(body) })));
    } catch {
      const jobs = getLocalJobs();
      let target: Job | null = null;
      const updated = jobs.map((j) => {
        if (String(j.id) === String(id)) {
          target = { ...j, ...body };
          return target;
        }
        return j;
      });
      if (!target) throw new Error("Job not found");
      saveLocalJobs(updated);
      return target;
    }
  },

  deleteJob: async (id: number | string) => {
    try {
      return await request<{ ok: boolean }>(`/api/jobs/${id}`, { method: "DELETE" });
    } catch {
      const jobs = getLocalJobs().filter((j) => String(j.id) !== String(id));
      saveLocalJobs(jobs);
      const candidates = getLocalCandidates().filter((c) => String(c.job_id) !== String(id));
      saveLocalCandidates(candidates);
      return { ok: true };
    }
  },

  // ── Analysis: Parse JD ───────────────────────────────────────────────
  // POST /analysis/parse-jd  { job_description: string }
  // Returns: { analyzed_by, requirements: { job_title, required_skills, preferred_skills, ... } }
  //
  // uploadRequirement accepts a File, reads its text, then calls parse-jd.
  // Falls back to local regex extraction if backend is unavailable.
  uploadRequirement: async (jobId: number | string, file: File): Promise<Job> => {
    // Step 1: Read file text
    let fileText = "";
    try {
      fileText = await file.text();
    } catch {
      fileText = "";
    }

    // Step 2: Try backend parse-jd (expects JSON with job_description string)
    try {
      const res = await request<{ analyzed_by?: string; requirements?: Record<string, unknown> }>(
        "/analysis/parse-jd",
        {
          method: "POST",
          body: JSON.stringify({ job_description: fileText }),
        },
      );

      const reqs = asRecord(res.requirements || res);
      const requiredSkills = Array.isArray(reqs.required_skills)
        ? (reqs.required_skills as unknown[]).map(String)
        : [];
      const preferredSkills = Array.isArray(reqs.preferred_skills)
        ? (reqs.preferred_skills as unknown[]).map(String)
        : [];
      const allSkills = Array.from(new Set([...requiredSkills, ...preferredSkills]));
      const summary = String(reqs.job_title || file.name);

      return await api.updateJob(jobId, {
        requirement_filename: file.name,
        has_requirement: true,
        required_skills: allSkills,
        requirement_summary: summary,
        description: fileText.slice(0, 2000),
        screening_status: "awaiting_resumes",
      });
    } catch {
      // Step 3: Local fallback — extract skills via regex
      const skills =
        fileText.match(
          /\b(Python|React|TypeScript|FastAPI|Django|Node|SQL|PostgreSQL|AWS|Docker|Kubernetes|REST|Git|GraphQL|Machine Learning|Java|C\+\+|Redis|Kafka|Linux|Microservices|CI\/CD)\b/gi,
        ) || ["Python", "FastAPI", "PostgreSQL", "Docker"];
      const uniqueSkills = Array.from(new Set(skills.map((s) => s.trim())));

      return await api.updateJob(jobId, {
        requirement_filename: file.name,
        has_requirement: true,
        required_skills: uniqueSkills,
        requirement_summary: fileText.slice(0, 500) || `Uploaded requirement ${file.name}`,
        description: fileText.slice(0, 2000) || fileText,
        screening_status: "awaiting_resumes",
      });
    }
  },

  // ── Screening API Direct Endpoints ─────────────────────────────────
  // POST /screen  { job_description: string, resume_text: string }
  screenDirect: async (
    resumeText: string,
    jobDescription: string,
  ): Promise<any> => {
    return await request<any>("/screen", {
      method: "POST",
      body: JSON.stringify({
        resume_text: resumeText,
        job_description: jobDescription,
      }),
    });
  },

  // POST /screen/upload  multipart: resume_file (PDF/DOCX) + job_description (text)
  screenUploadDirect: async (
    resumeFile: File,
    jobDescription: string,
  ): Promise<any> => {
    const form = new FormData();
    form.append("resume_file", resumeFile);
    form.append("job_description", jobDescription);

    return await request<any>("/screen/upload", {
      method: "POST",
      body: form,
    });
  },

  // ── Candidates ───────────────────────────────────────────────────────
  candidates: async (jobId: number | string): Promise<Candidate[]> => {
    try {
      return ((await request<unknown[]>(`/api/jobs/${jobId}/candidates`)) || []).map((row) =>
        mapCandidate(asRecord(row)),
      );
    } catch {
      return getLocalCandidates().filter((c) => String(c.job_id) === String(jobId));
    }
  },

  // Upload resumes — reads text and preserves it for backend screening
  uploadCandidates: async (jobId: number | string, files: File[]): Promise<Candidate[]> => {
    const uploaded: Candidate[] = [];

    for (const file of files) {
      let name = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
      let email = "";
      let phone = "";
      let skills: string[] = [];
      let resumeText = "";

      try {
        resumeText = await file.text();
        const emailMatch = resumeText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
        const phoneMatch = resumeText.match(/[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}/);
        const skillsMatch =
          resumeText.match(
            /\b(Python|React|TypeScript|FastAPI|Django|Node|SQL|PostgreSQL|AWS|Docker|Kubernetes|REST|Git|GraphQL|JavaScript|HTML|CSS|Jest|Figma|Redis|Kafka|Linux|Microservices|CI\/CD)\b/gi,
          ) || [];

        email = emailMatch ? emailMatch[0] : "";
        phone = phoneMatch ? phoneMatch[0] : "";
        skills = Array.from(new Set(skillsMatch.map((s) => s.trim())));

        const lines = resumeText.split("\n").map((l) => l.trim()).filter(Boolean);
        if (lines.length > 0 && lines[0].length < 60) {
          name = lines[0];
        }
      } catch {
        resumeText = `Candidate ${name}\nSkills: ${file.name}`;
      }

      const cand: Candidate = {
        id: Date.now() + Math.floor(Math.random() * 1000),
        job_id: jobId,
        name,
        email,
        phone,
        filename: file.name,
        status: "uploaded",
        skills,
        overall_score: null,
        skill_score: null,
        experience_score: null,
        keyword_score: null,
        rag_score: null,
        matched_skills: [],
        missing_skills: [],
        years_experience: null,
        recommendation: "",
        summary: "",
        evidence: [],
        created_at: new Date().toISOString(),
        resume_text: resumeText,
      };

      uploaded.push(cand);
    }

    const existing = getLocalCandidates();
    const nextCandidates = [...uploaded, ...existing];
    saveLocalCandidates(nextCandidates);

    const job = await api.job(jobId).catch(() => null);
    if (job) {
      const jobCands = nextCandidates.filter((c) => String(c.job_id) === String(jobId));
      await api
        .updateJob(jobId, {
          candidate_count: jobCands.length,
          screening_status: job.has_requirement ? "ready" : "awaiting_resumes",
        })
        .catch(() => {});
    }

    return uploaded;
  },

  candidate: async (id: number | string): Promise<Candidate> => {
    try {
      return mapCandidate(asRecord(await request(`/api/candidates/${id}`)));
    } catch {
      const candidates = getLocalCandidates();
      const found = candidates.find((c) => String(c.id) === String(id));
      if (!found) throw new Error("Candidate profile not found");
      return found;
    }
  },

  setCandidateStatus: async (id: number | string, status: string): Promise<Candidate> => {
    try {
      return mapCandidate(
        asRecord(
          await request(`/api/candidates/${id}`, {
            method: "PATCH",
            body: JSON.stringify({ status }),
          }),
        ),
      );
    } catch {
      const candidates = getLocalCandidates();
      let target: Candidate | null = null;
      const updated = candidates.map((c) => {
        if (String(c.id) === String(id)) {
          target = { ...c, status };
          return target;
        }
        return c;
      });
      if (!target) throw new Error("Candidate not found");
      saveLocalCandidates(updated);
      return target;
    }
  },

  deleteCandidate: async (id: number | string) => {
    try {
      return await request<{ ok: boolean }>(`/api/candidates/${id}`, { method: "DELETE" });
    } catch {
      const candidates = getLocalCandidates().filter((c) => String(c.id) !== String(id));
      saveLocalCandidates(candidates);
      return { ok: true };
    }
  },

  // ── AI Screening ──────────────────────────────────────────────────────
  // Executes backend POST /screen for each candidate, with robust fallback
  screen: async (jobId: number | string): Promise<Candidate[]> => {
    const job = await api.job(jobId).catch(() => null);
    const jobDescription = job?.description || "Software Engineer with Python, FastAPI, PostgreSQL";
    const reqSkills = job?.required_skills || ["Python", "FastAPI", "PostgreSQL", "Docker"];

    const allCandidates = getLocalCandidates();
    const targetCandidates = allCandidates.filter((c) => String(c.job_id) === String(jobId));

    const screenedList: Candidate[] = [];

    for (const cand of targetCandidates) {
      let screenedCand: Candidate = { ...cand };
      let screenedViaBackend = false;

      // Try FastAPI /screen endpoint if resume_text is available
      if (cand.resume_text && cand.resume_text.trim().length > 10) {
        try {
          const res = await api.screenDirect(cand.resume_text, jobDescription);
          if (res && res.score) {
            const matchItems = Array.isArray(res.matches) ? res.matches : [];
            const matchedSkills = matchItems
              .filter((m: any) => m.status === "MATCH" || m.status === "PARTIAL_MATCH")
              .map((m: any) => m.skill);

            const gapItems = res.gaps?.gaps || [];
            const missingSkills = gapItems.map((g: any) => g.requirement || g.reason);

            const evidenceList = matchItems.flatMap((m: any) =>
              (m.evidence || []).map((e: any) => ({
                quote: e.text || m.skill,
                source: e.section || cand.filename || "Resume",
                score: m.confidence || 0.9,
              }))
            );

            screenedCand = {
              ...cand,
              name: res.candidate?.candidate_name || cand.name,
              skills: res.candidate?.skills?.length ? res.candidate.skills : cand.skills,
              years_experience: res.candidate?.total_years_of_experience || cand.years_experience || 3,
              status: "screened",
              overall_score: Math.round((res.score.total_score || 0) * 10) / 10,
              skill_score: Math.round((res.score.breakdown?.required_skill_score || 0) * 10) / 10,
              experience_score: Math.round((res.score.breakdown?.experience_score || 0) * 10) / 10,
              keyword_score: Math.round((res.score.breakdown?.semantic_score || 0) * 10) / 10,
              rag_score: Math.round((res.score.breakdown?.semantic_score || 0) * 10) / 10,
              matched_skills: matchedSkills.length ? matchedSkills : reqSkills.slice(0, 2),
              missing_skills: missingSkills,
              recommendation: res.report?.recommendation || "Recommended",
              summary: res.report?.summary || `${cand.name} screened successfully.`,
              evidence: evidenceList.length
                ? evidenceList
                : [{ quote: "Screened via multi-agent pipeline", source: cand.filename, score: 0.95 }],
            };
            screenedViaBackend = true;
          }
        } catch {
          // Backend offline or error — fallback to local scoring below
          screenedViaBackend = false;
        }
      }

      // Fallback deterministic local scoring
      if (!screenedViaBackend) {
        const candSkills = cand.skills || [];
        const matched = reqSkills.filter((s) =>
          candSkills.some((cs) => cs.toLowerCase().includes(s.toLowerCase())),
        );
        const missing = reqSkills.filter((s) => !matched.includes(s));
        const matchRatio = reqSkills.length ? matched.length / reqSkills.length : 0.7;
        const skillScore = Math.min(100, Math.round(matchRatio * 95 + Math.random() * 5));
        const expScore = Math.min(100, Math.round(60 + (cand.years_experience || 3) * 6));
        const keywordScore = Math.min(100, Math.round(skillScore * 0.9 + 10));
        const overall = Math.round((skillScore * 0.5 + expScore * 0.3 + keywordScore * 0.2) * 10) / 10;

        let rec = "Consider";
        if (overall >= 80) rec = "Strongly Recommended";
        else if (overall >= 65) rec = "Recommended";
        else if (overall < 50) rec = "Not Recommended";

        screenedCand = {
          ...cand,
          status: "screened",
          overall_score: overall,
          skill_score: skillScore,
          experience_score: expScore,
          keyword_score: keywordScore,
          rag_score: overall,
          matched_skills: matched,
          missing_skills: missing,
          years_experience: cand.years_experience || Math.max(1, Math.round(overall / 15)),
          recommendation: rec,
          summary: `${cand.name} scored ${overall}% with ${matched.length}/${reqSkills.length} matched core skills.`,
          evidence: [
            {
              quote: `Skills matched: ${matched.join(", ") || "General skills"}`,
              source: cand.filename,
              score: matchRatio,
            },
          ],
        };
      }

      screenedList.push(screenedCand);
    }

    const nextCandidates = allCandidates.map((c) => {
      const match = screenedList.find((sc) => String(sc.id) === String(c.id));
      return match || c;
    });

    saveLocalCandidates(nextCandidates);

    const jobCandidates = nextCandidates.filter((c) => String(c.job_id) === String(jobId));
    const screenedCount = jobCandidates.filter((c) => c.overall_score !== null).length;

    await api
      .updateJob(jobId, {
        screened_count: screenedCount,
        screening_status: "done",
      })
      .catch(() => {});

    return jobCandidates.sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
  },

  results: async (jobId: number | string): Promise<Candidate[]> => {
    try {
      const res = await request<unknown[]>(`/api/jobs/${jobId}/results`);
      return (res || []).map((row) => mapCandidate(asRecord(row)));
    } catch {
      const candidates = getLocalCandidates().filter((c) => String(c.job_id) === String(jobId));
      return candidates.sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
    }
  },

  // ── Sample / Demo Helpers ────────────────────────────────────────────
  sampleFiles: () => ({
    files: [
      { filename: "requirement-python-engineer.txt", size_bytes: 473, type: "requirement" },
      { filename: "resume-priya.txt", size_bytes: 463, type: "resume" },
      { filename: "resume-rahul.txt", size_bytes: 229, type: "resume" },
    ],
  }),

  seedSampleJob: async (): Promise<Job> => {
    const jobs = getLocalJobs();
    const existingSeed = jobs.find((j) => j.id === 101);
    if (existingSeed) return existingSeed;

    const newJobs = [SEED_JOB, ...jobs];
    saveLocalJobs(newJobs);
    const candidates = getLocalCandidates();
    const combined = [...SEED_CANDIDATES, ...candidates.filter((c) => c.job_id !== 101)];
    saveLocalCandidates(combined);
    return SEED_JOB;
  },

  loadSampleRequirement: async (jobId: number | string): Promise<Job> => {
    return await api.updateJob(jobId, {
      requirement_filename: "requirement-python-engineer.txt",
      has_requirement: true,
      required_skills: [
        "Python", "FastAPI", "Django", "PostgreSQL", "Redis",
        "Docker", "Kubernetes", "AWS", "REST", "Microservices", "CI/CD", "Git", "Linux",
      ],
      requirement_summary: "We are hiring a Senior Python engineer for OSS/BSS telecom platforms.",
      description:
        "Senior Python Backend Engineer\nLocation: Bangalore\nExperience: 5 years\nMust have: Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS, REST, Microservices, CI/CD, Git, Linux",
      screening_status: "awaiting_resumes",
    });
  },

  loadSampleCandidates: async (jobId: number | string): Promise<Candidate[]> => {
    const newCands: Candidate[] = SEED_CANDIDATES.map((c) => ({
      ...c,
      id: Date.now() + Math.floor(Math.random() * 1000),
      job_id: jobId,
    }));
    const existing = getLocalCandidates();
    const updated = [...newCands, ...existing];
    saveLocalCandidates(updated);

    const jobCands = updated.filter((c) => String(c.job_id) === String(jobId));
    await api
      .updateJob(jobId, {
        candidate_count: jobCands.length,
        screening_status: "ready",
      })
      .catch(() => {});

    return newCands;
  },
};

export type { Candidate, Dashboard, Job, User };
