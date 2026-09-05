import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { recClass, recLabel, scoreColor, statusClass } from "../labels";
import type { Candidate } from "../types";

export function CandidatePage() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .candidate(Number(id))
      .then(setCandidate)
      .catch((err) => setError(err.message));
  }, [id]);

  async function setStatus(status: string) {
    if (!candidate) return;
    setCandidate(await api.setCandidateStatus(candidate.id, status));
  }

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!candidate) return <p className="text-slate-500">Loading candidate…</p>;

  const metrics = [
    { label: "Overall", value: candidate.overall_score },
    { label: "Skills", value: candidate.skill_score },
    { label: "Experience", value: candidate.experience_score },
    { label: "Keywords", value: candidate.keyword_score },
  ];

  return (
    <div className="space-y-6">
      <Link to={`/jobs/${candidate.job_id}`} className="text-sm text-slate-500 hover:text-ink-900">
        ← Back to role
      </Link>
      <div className="rounded-3xl bg-ink-950 p-8 text-white">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-accent-300">Candidate dossier</p>
            <h2 className="mt-2 font-display text-4xl">{candidate.name}</h2>
            <p className="mt-2 text-slate-300">
              {candidate.email || "No email parsed"} · {candidate.phone || "No phone parsed"}
            </p>
          </div>
          <div className="flex gap-2">
            <span className={`rounded-full px-3 py-1 text-sm ${statusClass(candidate.status)}`}>{candidate.status}</span>
            <span className={`rounded-full px-3 py-1 text-sm ${recClass(candidate.recommendation)}`}>
              {recLabel(candidate.recommendation)}
            </span>
          </div>
        </div>
        <p className="mt-6 max-w-3xl text-sm leading-6 text-slate-300">{candidate.summary || "Run screening on the role to generate an AI brief."}</p>
        <div className="mt-6 flex gap-2">
          <button onClick={() => setStatus("shortlisted")} className="rounded-xl bg-accent-500 px-4 py-2 text-sm font-semibold text-ink-950">
            Shortlist
          </button>
          <button onClick={() => setStatus("rejected")} className="rounded-xl bg-white/10 px-4 py-2 text-sm font-semibold">
            Reject
          </button>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-2xl bg-white p-5 shadow-card">
            <p className="text-sm text-slate-500">{metric.label}</p>
            <p className={`mt-2 text-3xl font-semibold ${scoreColor(metric.value)}`}>
              {metric.value == null ? "—" : metric.value}
            </p>
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl bg-white p-6 shadow-card">
          <h3 className="font-semibold">Matched skills</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {candidate.matched_skills.length === 0 && <p className="text-sm text-slate-500">None yet.</p>}
            {candidate.matched_skills.map((s) => (
              <span key={s} className="rounded-full bg-emerald-50 px-3 py-1 text-sm text-emerald-700">
                {s}
              </span>
            ))}
          </div>
          <h3 className="mt-6 font-semibold">Skill gaps</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {candidate.missing_skills.length === 0 && <p className="text-sm text-slate-500">No major gaps detected.</p>}
            {candidate.missing_skills.map((s) => (
              <span key={s} className="rounded-full bg-rose-50 px-3 py-1 text-sm text-rose-700">
                {s}
              </span>
            ))}
          </div>
        </div>
        <div className="rounded-2xl bg-white p-6 shadow-card">
          <h3 className="font-semibold">Resume extract</h3>
          <p className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap text-sm leading-6 text-slate-600">
            {candidate.resume_text || "No text extracted."}
          </p>
        </div>
      </div>
    </div>
  );
}
