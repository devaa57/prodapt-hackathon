import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Play, Sparkles, Star, X } from "lucide-react";
import { api } from "../api";
import { Dropzone } from "../components/Dropzone";
import { recClass, recLabel, scoreColor, statusClass } from "../labels";
import type { Candidate, Job } from "../types";

const tabs = ["Requirement", "Resumes", "Results"] as const;

export function JobWorkspacePage() {
  const { id } = useParams();
  const jobId = Number(id);
  const [job, setJob] = useState<Job | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [tab, setTab] = useState<(typeof tabs)[number]>("Requirement");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [nextJob, nextCandidates] = await Promise.all([api.job(jobId), api.results(jobId)]);
    setJob(nextJob);
    setCandidates(nextCandidates);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, [jobId]);

  async function onRequirement(files: File[]) {
    setBusy(true);
    setError("");
    try {
      setJob(await api.uploadRequirement(jobId, files[0]));
      setMessage(`Parsed ${files[0].name}`);
      setTab("Resumes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onLoadSampleRequirement() {
    setBusy(true);
    setError("");
    try {
      setJob(await api.loadSampleRequirement(jobId));
      setMessage("Loaded sample Python Engineer requirement document");
      setTab("Resumes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sample requirement");
    } finally {
      setBusy(false);
    }
  }

  async function onResumes(files: File[]) {
    setBusy(true);
    setError("");
    try {
      await api.uploadCandidates(jobId, files);
      await refresh();
      setMessage(`${files.length} resume${files.length === 1 ? "" : "s"} ingested`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onLoadSampleResumes() {
    setBusy(true);
    setError("");
    try {
      await api.loadSampleCandidates(jobId);
      await refresh();
      setMessage("Loaded sample candidate resumes (Priya Sharma & Rahul Mehta)");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sample resumes");
    } finally {
      setBusy(false);
    }
  }

  async function onScreen() {
    setBusy(true);
    setError("");
    try {
      const ranked = await api.screen(jobId);
      setCandidates(ranked);
      await refresh();
      setTab("Results");
      setMessage("Screening complete");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Screening failed");
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(candidate: Candidate, status: string) {
    const updated = await api.setCandidateStatus(candidate.id, status);
    setCandidates((prev) => prev.map((c) => (c.id === updated.id ? { ...c, ...updated } : c)));
  }

  if (!job) return <p className="text-slate-500">Loading workspace…</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link to="/jobs" className="text-sm text-slate-500 hover:text-ink-900">
            ← All roles
          </Link>
          <h2 className="mt-1 font-display text-3xl">{job.title}</h2>
          <p className="text-slate-500">
            {job.department || "General"} · {job.location || "Location TBD"} · {job.employment_type}
          </p>
        </div>
        <button
          onClick={onScreen}
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-xl bg-accent-500 px-4 py-2.5 text-sm font-semibold text-ink-950 hover:bg-accent-400 disabled:opacity-60"
        >
          <Play className="h-4 w-4" />
          Run AI screening
        </button>
      </div>

      {(message || error) && (
        <p className={`rounded-xl px-4 py-3 text-sm ${error ? "bg-rose-50 text-rose-700" : "bg-teal-50 text-teal-800"}`}>
          {error || message}
        </p>
      )}

      <div className="flex gap-2">
        {tabs.map((item) => (
          <button
            key={item}
            onClick={() => setTab(item)}
            className={`rounded-full px-4 py-2 text-sm font-medium ${
              tab === item ? "bg-ink-900 text-white" : "bg-white text-slate-500"
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      {tab === "Requirement" && (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="rounded-2xl bg-white p-6 shadow-card lg:col-span-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Requirement document</h3>
              <button
                onClick={onLoadSampleRequirement}
                disabled={busy}
                className="inline-flex items-center gap-1 text-xs font-medium text-accent-600 hover:underline disabled:opacity-60"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Use sample JD
              </button>
            </div>
            <p className="mb-4 mt-1 text-sm text-slate-500">PDF, DOCX, or TXT job description / requisition pack.</p>
            <Dropzone
              label="Drop the requirement file"
              hint="We’ll extract skills, tenure, and keywords automatically."
              accept=".pdf,.doc,.docx,.txt,.md"
              onFiles={onRequirement}
            />
            {job.requirement_filename && (
              <p className="mt-4 text-sm text-slate-600">
                Current file: <span className="font-medium">{job.requirement_filename}</span>
              </p>
            )}
          </div>
          <div className="rounded-2xl bg-white p-6 shadow-card lg:col-span-3">
            <h3 className="font-semibold">Extracted skills</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {job.required_skills.length === 0 && <p className="text-sm text-slate-500">Upload a document to populate the skill graph.</p>}
              {job.required_skills.map((skill) => (
                <span key={skill} className="rounded-full bg-teal-50 px-3 py-1 text-sm text-teal-800">
                  {skill}
                </span>
              ))}
            </div>
            {job.description && (
              <p className="mt-6 whitespace-pre-wrap text-sm leading-6 text-slate-600">{job.description.slice(0, 900)}</p>
            )}
          </div>
        </div>
      )}

      {tab === "Resumes" && (
        <div className="space-y-6">
          <div className="rounded-2xl bg-white p-6 shadow-card">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Candidate resumes</h3>
              <button
                onClick={onLoadSampleResumes}
                disabled={busy}
                className="inline-flex items-center gap-1 text-xs font-medium text-accent-600 hover:underline disabled:opacity-60"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Use sample resumes
              </button>
            </div>
            <p className="mb-4 mt-1 text-sm text-slate-500">Upload one or many CVs. Names, emails, and skills are parsed on ingest.</p>
            <Dropzone
              multiple
              label="Drop resumes here"
              hint="PDF, DOCX, or TXT · bulk upload supported"
              accept=".pdf,.doc,.docx,.txt"
              onFiles={onResumes}
            />
          </div>
          <div className="overflow-hidden rounded-2xl bg-white shadow-card">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Candidate</th>
                  <th className="px-4 py-3">File</th>
                  <th className="px-4 py-3">Skills</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c) => (
                  <tr key={c.id} className="border-t border-slate-100">
                    <td className="px-4 py-3">
                      <Link to={`/candidates/${c.id}`} className="font-medium hover:text-accent-600">
                        {c.name}
                      </Link>
                      <p className="text-xs text-slate-500">{c.email || "Email not detected"}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{c.filename}</td>
                    <td className="px-4 py-3 text-slate-500">{c.skills.slice(0, 4).join(", ") || "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusClass(c.status)}`}>{c.status}</span>
                    </td>
                  </tr>
                ))}
                {candidates.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                      No resumes uploaded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "Results" && (
        <div className="overflow-hidden rounded-2xl bg-white shadow-card">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">Rank</th>
                <th className="px-4 py-3">Candidate</th>
                <th className="px-4 py-3">Match</th>
                <th className="px-4 py-3">Recommendation</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c, index) => (
                <tr key={c.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-semibold text-slate-400">{index + 1}</td>
                  <td className="px-4 py-3">
                    <Link to={`/candidates/${c.id}`} className="font-medium hover:text-accent-600">
                      {c.name}
                    </Link>
                    <p className="max-w-md text-xs text-slate-500">{c.summary || "Run screening to generate an AI summary."}</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className={`text-lg font-semibold ${scoreColor(c.overall_score)}`}>
                      {c.overall_score == null ? "—" : `${c.overall_score}`}
                    </p>
                    <div className="mt-1 h-1.5 w-28 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full bg-accent-500" style={{ width: `${c.overall_score || 0}%` }} />
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${recClass(c.recommendation)}`}>
                      {recLabel(c.recommendation)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setStatus(c, "shortlisted")}
                        className="rounded-lg p-2 text-teal-600 hover:bg-teal-50"
                        title="Shortlist"
                      >
                        <Star className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setStatus(c, "rejected")}
                        className="rounded-lg p-2 text-rose-600 hover:bg-rose-50"
                        title="Reject"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {candidates.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    Upload resumes and run screening to see ranked results.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
